variable "db_password" {
  description = "Password for RDS PostgreSQL"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "gps_trace_api_token" {
  description = "GPS-Trace API Token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openweathermap_api_key" {
  description = "OpenWeatherMap API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "iot_api_key" {
  description = "IoT Gateway API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "traffic_api_key" {
  description = "Traffic API Key (Google/HERE/Mapbox)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "glih_admin_password" {
  description = "Seed password for admin@glih.ops account (force_password_change=true on first login)"
  type        = string
  sensitive   = true
}

variable "glih_dispatcher_password" {
  description = "Seed password for sample dispatcher accounts (force_password_change=true on first login)"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "HS256 JWT signing secret — must be at least 32 characters"
  type        = string
  sensitive   = true
}
