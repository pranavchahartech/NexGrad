# Puppet Module: nexgrad_frontend
class nexgrad_frontend {
  package { 'nginx':
    ensure => installed,
  }

  file { '/etc/nginx/sites-available/nexgrad':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "# NexGrad Nginx Configuration managed by Puppet\nserver {\n    listen 80;\n    server_name _;\n    location /static/ {\n        alias /opt/nexgrad/frontend/static/;\n    }\n    location / {\n        proxy_pass http://127.0.0.1:8000;\n    }\n}\n",
    notify  => Service['nginx'],
  }

  file { '/etc/nginx/sites-enabled/nexgrad':
    ensure => link,
    target => '/etc/nginx/sites-available/nexgrad',
    notify => Service['nginx'],
  }

  service { 'nginx':
    ensure => running,
    enable => true,
  }
}

