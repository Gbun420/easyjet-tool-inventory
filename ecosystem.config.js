module.exports = {
  apps: [
    {
      name: 'easyjet-tool-inventory',
      script: 'python3',
      args: 'demo_app.py',
      cwd: '/home/user/webapp',
      env: {
        PYTHONPATH: '/home/user/webapp'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      log_file: './logs/combined.log',
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      time: true
    }
  ]
};