module.exports = {
  apps: [
    {
      name: 'backend',
      script: 'run.py',
      cwd: './backend',
      interpreter: 'python',
      env: {
        NODE_ENV: 'development'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    },
    {
      name: 'frontend',
      script: 'npm',
      args: 'run serve',
      cwd: './',
      env: {
        NODE_ENV: 'development'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ]
}; 