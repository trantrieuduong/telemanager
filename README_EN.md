# TeleManager - Multi-Account Telegram Desktop Manager

TeleManager is a lightweight, high-performance Windows desktop application designed to manage and launch multiple Telegram accounts simultaneously in completely isolated sandboxes. It features dedicated proxy management, real-time process monitoring, safe profile operations, and session protection.

This project is an enhanced and refactored fork based on the original repository: [telemanager-app/telemanager](https://github.com/telemanager-app/telemanager).

---

## Key Features

- **Unlimited Accounts**: Create, organize, and manage as many Telegram profiles as needed (Work, Personal, Crypto, Automation) on a single Windows machine.
- **Strict Session Isolation**: Every profile operates within its own dedicated directory using Telegram's native `-workdir` argument. Cache, chat databases, and session credentials (`tdata`) are never mixed.
- **Real-Time Process Monitoring**: Automatically detects active Telegram instances and accurately reflects current status (`Running` or `Closed`).
- **Safe Process Termination**: Allows users to gracefully close running Telegram processes directly from the user interface.
- **Data Integrity Protection**: Deletion and folder renaming are strictly locked while a profile is running, preventing file locks (`PermissionError`) and avoiding session corruption.
- **Dedicated Proxy Management**:
  - Full support for SOCKS5, HTTP, and MTProto protocols per account.
  - Quick-paste parser for standard proxy strings (`host:port:user:pass` or URLs).
  - Built-in socket latency testing (in milliseconds) before launching.
  - Generates standard `tg://` deep links to automatically populate proxy configurations in Telegram Desktop.
- **Fast Search and Live Filtering**: Quickly filter through accounts by display name, folder name, or custom notes.
- **Custom Display Names**: Support for descriptive names and notes (phone numbers, creation dates, purpose).
- **Safe Profile Backup and Migration**: Export and import profiles as `.zip` archives, enabling safe migration across computers without triggering re-authentication.
- **Modern Windows Interface**: Native Windows 11 aesthetics built with CustomTkinter, fully supporting Dark Mode.

---

## Project Structure

```text
telemanager/
├── bin/
│   └── Telegram.exe             # Official Telegram Portable binary
├── profiles/
│   └── <profile_name>/          # Individual profile directories
│       ├── tdata/               # Telegram session data
│       └── meta.json            # Profile configuration (display name, notes, proxy)
├── src/
│   ├── __init__.py
│   ├── config.py                # System paths and unified sys.executable handling
│   ├── models/
│   │   ├── __init__.py
│   │   └── profile.py           # Profile and ProxyConfig data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── process_service.py   # Process tracking, detection, and termination
│   │   ├── profile_service.py   # Profile CRUD, validation, backup, and restore
│   │   └── proxy_service.py     # Proxy parsing, latency test, and deep-link generation
│   └── ui/
│       ├── __init__.py
│       ├── app.py               # Main window controller and lifecycle loop
│       ├── components/
│       │   ├── __init__.py
│       │   ├── header.py        # Application header with live search
│       │   └── profile_card.py  # Profile item card with status badges and actions
│       └── dialogs/
│           ├── __init__.py
│           ├── profile_dialog.py # Create and edit profile dialog
│           └── proxy_dialog.py   # Proxy configuration and testing dialog
├── appicon.ico                  # Application icon
├── main.py                      # Application entrypoint
├── README.md                    # Vietnamese documentation
└── README_EN.md                 # English documentation
```

---

## Getting Started

### Prerequisites
- Operating System: Windows 10 or Windows 11
- Python: Version 3.10 or higher

### 1. Install Dependencies
```bash
pip install customtkinter pillow
```

### 2. Add Telegram Executable
1. Download the official **Telegram Desktop Portable** version from [desktop.telegram.org](https://desktop.telegram.org).
2. Create a folder named `bin` in the project root if it does not already exist.
3. Place `Telegram.exe` inside the `bin/` directory.

### 3. Launch the Application
```bash
python main.py
```

---

## Compiling to Standalone Executable (.exe)

You can compile the application into a standalone executable using `pyinstaller`:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the build command:
   ```bash
   pyinstaller --noconsole --onefile --icon=appicon.ico --name="TeleManager" main.py
   ```

3. Once compilation finishes, the standalone binary `TeleManager.exe` will be located in the `dist/` directory. Place it in a folder containing the `bin/` directory (with `Telegram.exe`) and `appicon.ico` for full functionality.

---

## Account Security and Anti-Ban Guidelines

1. **Avoid Opening the Same Session Concurrently**: Running identical profile copies simultaneously on separate machines with different IP addresses triggers security flags in Telegram's fraud detection system, often resulting in immediate session termination.
2. **Always Close Telegram Before Backing Up**: Copying or archiving a profile directory while Telegram is running can lead to corrupted SQLite databases or uncommitted data.
3. **Use High-Quality Proxies**: Static residential SOCKS5 proxies or 4G/5G mobile proxies are strongly recommended. Avoid cheap datacenter or hosting provider IP ranges (AWS, DigitalOcean, Hetzner, etc.), as Telegram frequently flags these networks.
4. **Maintain Consistent IP Geolocation**: Keep an account bound to the same proxy or consistent network region. Rapid geolocation changes in short timeframes significantly increase verification checkpoints.

---

## Disclaimer

- TeleManager is an open-source utility created strictly to help users manage their own personal and authorized accounts on their local computers.
- TeleManager does not modify Telegram binaries, does not inject code into Telegram's process memory, and does not alter Telegram's core encryption or network protocols.
- Users are solely responsible for complying with the [Telegram Terms of Service](https://telegram.org/tos). The author and contributors accept no liability or responsibility for any account restrictions, spam limitations, or bans resulting from user misuse, bad proxies, or policy violations.

---

## License

This project is licensed under the [MIT License](LICENSE).

The original project was created by **Eyuel Engida** at [https://github.com/telemanager-app/telemanager](https://github.com/telemanager-app/telemanager). All modular refactoring, process supervision, dedicated proxy management, and session safety features have been developed in this enhanced version.
