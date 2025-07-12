#!/usr/bin/env node

import { program } from 'commander';
import * as fs from 'fs';
import * as path from 'path';
import {
  tryRegisterUserLevelHost,
  colorText,
  registerWithElevatedPermissions,
  ensureExecutionPermissions,
  tryUnregisterUserLevelHost,
  unregisterWithElevatedPermissions,
  checkRegistrationStatus,
} from './scripts/utils';

// Import writeNodePath from postinstall
async function writeNodePath(): Promise<void> {
  try {
    const nodePath = process.execPath;
    const nodePathFile = path.join(__dirname, 'node_path.txt');

    console.log(colorText(`Writing Node.js path: ${nodePath}`, 'blue'));
    fs.writeFileSync(nodePathFile, nodePath, 'utf8');
    console.log(colorText('✓ Node.js path written for run_host scripts', 'green'));
  } catch (error: any) {
    console.warn(colorText(`⚠️ Failed to write Node.js path: ${error.message}`, 'yellow'));
  }
}

program
  .version(require('../package.json').version)
  .description('Mcp Chrome Bridge - Local service for communicating with Chrome extension');

// Register Native Messaging host
program
  .command('register')
  .description('Register Native Messaging host')
  .option('-f, --force', 'Force re-registration')
  .option('-s, --system', 'Use system-level installation (requires administrator/sudo privileges)')
  .action(async (options) => {
    try {
      // Write Node.js path for run_host scripts
      await writeNodePath();

      // Detect if running with root/administrator privileges
      const isRoot = process.getuid && process.getuid() === 0; // Unix/Linux/Mac

      let isAdmin = false;
      if (process.platform === 'win32') {
        try {
          isAdmin = require('is-admin')(); // Windows requires additional package
        } catch (error) {
          console.warn(
            colorText('Warning: Unable to detect administrator privileges on Windows', 'yellow'),
          );
          isAdmin = false;
        }
      }

      const hasElevatedPermissions = isRoot || isAdmin;

      // If --system option is specified or running with root/administrator privileges
      if (options.system || hasElevatedPermissions) {
        await registerWithElevatedPermissions();
        console.log(
          colorText('System-level Native Messaging host registered successfully!', 'green'),
        );
        console.log(
          colorText(
            'You can now use connectNative in Chrome extension to connect to this service.',
            'blue',
          ),
        );
      } else {
        // Regular user-level installation
        console.log(colorText('Registering user-level Native Messaging host...', 'blue'));
        const success = await tryRegisterUserLevelHost();

        if (success) {
          console.log(colorText('Native Messaging host registered successfully!', 'green'));
          console.log(
            colorText(
              'You can now use connectNative in Chrome extension to connect to this service.',
              'blue',
            ),
          );
        } else {
          console.log(
            colorText(
              'User-level registration failed, please try the following methods:',
              'yellow',
            ),
          );
          console.log(colorText('  1. sudo mcp-chrome-bridge register', 'yellow'));
          console.log(colorText('  2. mcp-chrome-bridge register --system', 'yellow'));
          process.exit(1);
        }
      }
    } catch (error: any) {
      console.error(colorText(`Registration failed: ${error.message}`, 'red'));
      process.exit(1);
    }
  });

// Fix execution permissions
program
  .command('fix-permissions')
  .description('Fix execution permissions for native host files')
  .action(async () => {
    try {
      console.log(colorText('Fixing execution permissions...', 'blue'));
      await ensureExecutionPermissions();
      console.log(colorText('✓ Execution permissions fixed successfully!', 'green'));
    } catch (error: any) {
      console.error(colorText(`Failed to fix permissions: ${error.message}`, 'red'));
      process.exit(1);
    }
  });

// Update port in stdio-config.json
program
  .command('update-port <port>')
  .description('Update the port number in stdio-config.json')
  .action(async (port: string) => {
    try {
      const portNumber = parseInt(port, 10);
      if (isNaN(portNumber) || portNumber < 1 || portNumber > 65535) {
        console.error(colorText('Error: Port must be a valid number between 1 and 65535', 'red'));
        process.exit(1);
      }

      const configPath = path.join(__dirname, 'mcp', 'stdio-config.json');

      if (!fs.existsSync(configPath)) {
        console.error(colorText(`Error: Configuration file not found at ${configPath}`, 'red'));
        process.exit(1);
      }

      const configData = fs.readFileSync(configPath, 'utf8');
      const config = JSON.parse(configData);

      const currentUrl = new URL(config.url);
      currentUrl.port = portNumber.toString();
      config.url = currentUrl.toString();

      fs.writeFileSync(configPath, JSON.stringify(config, null, 4));

      console.log(colorText(`✓ Port updated successfully to ${portNumber}`, 'green'));
      console.log(colorText(`Updated URL: ${config.url}`, 'blue'));
    } catch (error: any) {
      console.error(colorText(`Failed to update port: ${error.message}`, 'red'));
      process.exit(1);
    }
  });

// Unregister Native Messaging host
program
  .command('unregister')
  .description('Unregister Native Messaging host')
  .option('-s, --system', 'Use system-level uninstallation (requires administrator/sudo privileges)')
  .action(async (options) => {
    try {
      // Check current registration status
      const status = checkRegistrationStatus();

      if (!status.userLevel && !status.systemLevel) {
        console.log(colorText('No Native Messaging host registration found.', 'yellow'));
        return;
      }

      console.log(colorText('Current registration status:', 'blue'));
      console.log(colorText(`  User-level: ${status.userLevel ? 'Registered' : 'Not registered'}`, status.userLevel ? 'green' : 'yellow'));
      console.log(colorText(`  System-level: ${status.systemLevel ? 'Registered' : 'Not registered'}`, status.systemLevel ? 'green' : 'yellow'));

      // Detect if running with root/administrator privileges
      const isRoot = process.getuid && process.getuid() === 0; // Unix/Linux/Mac

      let isAdmin = false;
      if (process.platform === 'win32') {
        try {
          isAdmin = require('is-admin')(); // Windows requires additional package
        } catch (error) {
          console.warn(
            colorText('Warning: Unable to detect administrator privileges on Windows', 'yellow'),
          );
          isAdmin = false;
        }
      }

      const hasElevatedPermissions = isRoot || isAdmin;

      // If --system option is specified or running with root/administrator privileges
      if (options.system || hasElevatedPermissions) {
        if (status.systemLevel) {
          await unregisterWithElevatedPermissions();
          console.log(
            colorText('System-level Native Messaging host unregistered successfully!', 'green'),
          );
        } else {
          console.log(colorText('No system-level registration found.', 'yellow'));
        }
      } else {
        // Regular user-level unregistration
        if (status.userLevel) {
          console.log(colorText('Unregistering user-level Native Messaging host...', 'blue'));
          const success = await tryUnregisterUserLevelHost();

          if (success) {
            console.log(colorText('User-level Native Messaging host unregistered successfully!', 'green'));
          } else {
            console.log(
              colorText(
                'User-level unregistration failed, please try with administrator privileges:',
                'yellow',
              ),
            );
            console.log(colorText('  1. sudo mcp-chrome-bridge unregister', 'yellow'));
            console.log(colorText('  2. mcp-chrome-bridge unregister --system', 'yellow'));
            process.exit(1);
          }
        } else {
          console.log(colorText('No user-level registration found.', 'yellow'));
        }

        // Also remind about system-level if it exists
        if (status.systemLevel) {
          console.log(colorText('Note: System-level registration still exists.', 'yellow'));
          console.log(colorText('To remove it, run: mcp-chrome-bridge unregister --system', 'blue'));
        }
      }
    } catch (error: any) {
      console.error(colorText(`Unregistration failed: ${error.message}`, 'red'));
      process.exit(1);
    }
  });

// Check registration status
program
  .command('status')
  .description('Check Native Messaging host registration status')
  .action(async () => {
    try {
      console.log(colorText('Checking Native Messaging host registration status...', 'blue'));

      const status = checkRegistrationStatus();

      console.log(colorText('\nRegistration Status:', 'blue'));
      console.log(colorText(`  User-level: ${status.userLevel ? 'Registered ✓' : 'Not registered ✗'}`, status.userLevel ? 'green' : 'red'));
      console.log(colorText(`  System-level: ${status.systemLevel ? 'Registered ✓' : 'Not registered ✗'}`, status.systemLevel ? 'green' : 'red'));

      if (!status.userLevel && !status.systemLevel) {
        console.log(colorText('\n📝 To register:', 'yellow'));
        console.log(colorText('  User-level:   mcp-chrome-bridge register', 'cyan'));
        console.log(colorText('  System-level: mcp-chrome-bridge register --system', 'cyan'));
      } else {
        console.log(colorText('\n📝 To unregister:', 'yellow'));
        if (status.userLevel) {
          console.log(colorText('  User-level:   mcp-chrome-bridge unregister', 'cyan'));
        }
        if (status.systemLevel) {
          console.log(colorText('  System-level: mcp-chrome-bridge unregister --system', 'cyan'));
        }
      }
    } catch (error: any) {
      console.error(colorText(`Status check failed: ${error.message}`, 'red'));
      process.exit(1);
    }
  });

program.parse(process.argv);

// If no command provided, show help
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
