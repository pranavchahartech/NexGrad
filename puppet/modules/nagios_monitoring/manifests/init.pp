# Puppet Module: nagios_monitoring
class nagios_monitoring {
  package { ['nagios-nrpe-server', 'monitoring-plugins']:
    ensure => installed,
  }

  service { 'nagios-nrpe-server':
    ensure => running,
    enable => true,
  }
}

