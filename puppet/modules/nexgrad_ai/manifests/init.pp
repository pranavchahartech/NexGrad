# Puppet Module: nexgrad_ai
class nexgrad_ai (
  String $app_user = 'nexgrad',
  String $ai_root  = '/opt/nexgrad/ai-service',
) {
  file { '/etc/systemd/system/nexgrad-ai.service':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "[Unit]\nDescription=NexGrad AI Microservice Daemon\nAfter=network.target\n\n[Service]\nUser=${app_user}\nWorkingDirectory=${ai_root}\nExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8001\nRestart=always\nRestartSec=5\n\n[Install]\nWantedBy=multi-user.target\n",
    notify  => Service['nexgrad-ai'],
  }

  service { 'nexgrad-ai':
    ensure => running,
    enable => true,
  }
}

