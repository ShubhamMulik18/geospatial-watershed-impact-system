export interface User {
  id: string
  username: string
  is_active: boolean
  created_at: string
}

export interface LoginResponse {
  user: User
  access_token: string
  token_type: string
  expires_in: number
}

export interface LogoutResponse {
  message: string
}

