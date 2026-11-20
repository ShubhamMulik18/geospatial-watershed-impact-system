import type { ReactNode } from 'react'

type PageContainerProps = {
  children: ReactNode
}

function PageContainer({ children }: PageContainerProps) {
  return (
    <main className="flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        {children}
      </div>
    </main>
  )
}

export default PageContainer