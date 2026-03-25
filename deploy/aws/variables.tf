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
