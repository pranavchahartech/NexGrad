# ==============================================================================
# Puppet Primary Manifest (site.pp)
# Enforces system configuration baselines across all NexGrad infrastructure
# ==============================================================================

# Global Package Defaults
Package {
  allow_virtual => true,
}

# Node Class Mapping
node default {
  include nexgrad_backend
  include nexgrad_frontend
  include nagios_monitoring
}

node /^app\d+\.production\.nexgrad\.internal$/ {
  include nexgrad_backend
  include nagios_monitoring
}

node /^web\d+\.production\.nexgrad\.internal$/ {
  include nexgrad_frontend
  include nagios_monitoring
}

