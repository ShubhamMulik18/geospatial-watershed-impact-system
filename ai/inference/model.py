"""Shared MobileNetV2 structure for watershed training and inference.

Save as ai/inference/model.py. From the project root, run:
    .venv-ai/bin/python -m ai.inference.model --check

The check uses random weights and temporary tensors on CPU. It does not read
photographs, download weights, assign splits, save a checkpoint or run an
optimizer. Its output is a software check, not a trained prediction or accuracy.

Future training must pass train_dataset.class_ids as the class order and use
pretrained=True explicitly. That loads MobileNet_V2_Weights.IMAGENET1K_V2
(downloading them if necessary), matching ai/inference/preprocess.py. The new
classification head still needs watershed training. A frozen backbone keeps
both its parameters and its BatchNorm running statistics fixed.

Future inference must pass the exact ordered class IDs from the validated model
bundle, construct with pretrained=False, load the trusted state_dict strictly,
then call eval() and use torch.inference_mode(). Class order must be exported
separately with the state_dict; tensors alone cannot identify class meanings.

The forward method returns raw logits, not probabilities or public API results.
Other/Unknown fallback and confidence thresholds belong in the future predictor.
Normal imports of this module do not import the training/data-loading modules.

Reference:
https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v2.html
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

if __name__ == "__main__" and not __package__:
    raise SystemExit(
        "From the project root, run: "
        ".venv-ai/bin/python -m ai.inference.model --check"
    )

import torch
from torch import Tensor, nn
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2


class WatershedMobileNetV2(nn.Module):
    """A reusable network whose output columns follow the caller's class order.

    The caller validates membership against the public config or model bundle.
    This class preserves order and rejects malformed or repeated IDs. It never
    infers labels from filenames, alphabetic sorting or available photographs.
    """

    def __init__(
        self,
        class_ids: Sequence[str],
        *,
        pretrained: bool,
        freeze_backbone: bool = True,
    ) -> None:
        super().__init__()
        if isinstance(class_ids, (str, bytes)) or not isinstance(class_ids, Sequence):
            raise ValueError("class_ids must be an ordered list or tuple of IDs.")
        ordered = tuple(class_ids)
        if (
            len(ordered) < 2
            or any(not isinstance(item, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", item)
                   for item in ordered)
            or len(set(ordered)) != len(ordered)
        ):
            raise ValueError("Provide at least two distinct, valid class IDs.")
        if not isinstance(pretrained, bool) or not isinstance(freeze_backbone, bool):
            raise ValueError("pretrained and freeze_backbone must be True or False.")

        self._class_ids = ordered
        weights = MobileNet_V2_Weights.IMAGENET1K_V2 if pretrained else None
        self.network = mobilenet_v2(weights=weights)
        old_head = self.network.classifier[-1]
        if not isinstance(old_head, nn.Linear):
            raise RuntimeError("Unexpected torchvision MobileNetV2 classifier structure.")
        self.network.classifier[-1] = nn.Linear(old_head.in_features, len(ordered))
        self.set_backbone_frozen(freeze_backbone)

    @property
    def class_ids(self) -> tuple[str, ...]:
        return self._class_ids

    @property
    def backbone_frozen(self) -> bool:
        return self._backbone_frozen

    def set_backbone_frozen(self, frozen: bool) -> None:
        """Freeze/unfreeze features; build a new optimizer after changing this.

        Calling train() later will preserve the requested freeze policy.
        The classification head remains trainable. Fine-tuning configuration
        and optimizer selection belong to the future training script.
        """
        if not isinstance(frozen, bool):
            raise ValueError("frozen must be True or False.")
        self._backbone_frozen = frozen
        self.network.features.requires_grad_(not frozen)
        if frozen:
            for parameter in self.network.features.parameters():
                parameter.grad = None
        self.network.features.train(self.training and not frozen)

    def train(self, mode: bool = True) -> WatershedMobileNetV2:
        super().train(mode)
        if self.backbone_frozen:
            self.network.features.eval()
        return self

    def forward(self, images: Tensor) -> Tensor:
        """Map a preprocessed (N, 3, 224, 224) batch to (N, number_of_classes)."""
        return self.network(images)


def check_structure(class_ids: Sequence[str]) -> None:
    """Exercise batch shapes, gradients and frozen BatchNorm without learning."""
    torch.manual_seed(42)
    model = WatershedMobileNetV2(class_ids, pretrained=False, freeze_backbone=True)
    model.eval()
    for batch_size in (1, 4):
        inputs = torch.randn(batch_size, 3, 224, 224, device="cpu", dtype=torch.float32)
        with torch.inference_mode():
            scores = model(inputs)
        if (
            tuple(scores.shape) != (batch_size, len(class_ids))
            or scores.dtype != torch.float32
            or scores.device.type != "cpu"
            or not torch.isfinite(scores).all().item()
        ):
            raise ValueError("Expected finite CPU float32 scores with one column per class.")
        print(f"SHAPE: images={tuple(inputs.shape)}, scores={tuple(scores.shape)}")

    saved_buffers = {
        name: value.clone() for name, value in model.network.features.named_buffers()
    }
    model.train()
    if any(module.training for module in model.network.features.modules()):
        raise ValueError("Frozen feature layers unexpectedly entered training mode.")
    if not model.network.classifier.training:
        raise ValueError("Classification head did not enter training mode.")
    if any(parameter.requires_grad for parameter in model.network.features.parameters()):
        raise ValueError("Frozen backbone parameters unexpectedly require gradients.")
    inputs = torch.randn(2, 3, 224, 224, device="cpu", dtype=torch.float32)
    labels = torch.tensor([0, 1], device="cpu", dtype=torch.int64)
    loss = nn.functional.cross_entropy(model(inputs), labels)
    loss.backward()  # Gradient check only: no optimizer is created or stepped.
    if any(parameter.grad is not None for parameter in model.network.features.parameters()):
        raise ValueError("Frozen backbone unexpectedly received gradients.")
    for parameter in model.network.classifier.parameters():
        if parameter.grad is None or not torch.isfinite(parameter.grad).all().item():
            raise ValueError("Classification head did not receive finite gradients.")
    for name, value in model.network.features.named_buffers():
        if not torch.equal(saved_buffers[name], value):
            raise ValueError(f"Frozen backbone buffer changed: {name}.")
    print("PASS: head gradients; frozen backbone parameters and BatchNorm statistics.")

    model.set_backbone_frozen(False)
    model.train()
    if not all(parameter.requires_grad for parameter in model.network.features.parameters()):
        raise ValueError("Backbone did not unfreeze.")
    if not all(module.training for module in model.network.features.modules()):
        raise ValueError("Unfrozen feature layers did not enter training mode.")
    model.eval()
    if any(module.training for module in model.modules()):
        raise ValueError("Evaluation mode did not disable all training modes.")
    print("PASS: backbone unfreeze and evaluation mode.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the watershed MobileNetV2 structure.")
    parser.add_argument("--check", action="store_true", required=True,
                        help="Use random weights and temporary CPU inputs; no downloads")
    parser.add_argument("--classes", type=Path,
                        default=Path(__file__).resolve().parents[1] / "config/classes.json")
    args = parser.parse_args(argv)
    try:
        # Only this development check reads project config. Training/inference
        # pass their already-validated class order to the constructor directly.
        from ai.training.validate_dataset import load_class_ids

        public_ids = load_class_ids(args.classes)
        class_ids = tuple(item for item in public_ids if item != "other_unknown")
        print("Mode: structure check (random weights; CPU)")
        print("Class order from configuration:")
        for index, class_id in enumerate(class_ids):
            print(f"  {index}: {class_id}")
        check_structure(class_ids)
        print("\nPASS: Model structure check completed.")
        print("Software check only; no trained predictions or accuracy results.")
        print("No photographs, manifests, splits or model files were changed.")
        return 0
    except (OSError, UnicodeError, ValueError, ImportError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
