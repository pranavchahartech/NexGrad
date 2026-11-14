# Puppet Module: nexgrad_backend
class nexgrad_backend (
  String $app_user  = 'nexgrad',
  String $app_root  = '/opt/nexgrad/backend',
  Integer $workers  = 3,
) {
  user { $app_user:
    ensure     => present,
    managehome => true,
    shell      => '/bin/bash',
  }

  package { ['python3', 'python3-pip', 'python3-venv', 'libpq-dev']:
    ensure => installed,
  }

  file { [$app_root, '/var/log/nexgrad']:
    ensure => directory,
    owner  => $app_user,
    group  => $app_user,
    mode   => '0755',
  }

  file { '/etc/systemd/system/nexgrad-backend.service':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "[Unit]\nDescription=NexGrad Django Backend Daemon\nAfter=network.target\n\n[Service]\nUser=${app_user}\nWorkingDirectory=${app_root}\nEnvironmentFile=/etc/nexgrad/nexgrad.env\nExecStart=/opt/nexgrad/venv/bin/gunicorn nexgrad.wsgi:application --bind 0.0.0.0:8000 --workers ${workers}\nRestart=always\nRestartSec=5\n\n[Install]\nWantedBy=multi-user.target\n",
    notify  => Service['nexgrad-backend'],
  }

  service { 'nexgrad-backend':
    ensure => running,
    enable => true,
  }
}

