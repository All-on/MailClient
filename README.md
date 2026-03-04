<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/your-username/MailClient">
    <img src="assets/images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">MailClient</h3>

  <p align="center">
    A cross-platform email client with end-to-end encryption using SMTP and POP3 protocols!<br/>
  </p>
</div>

## About The Project

MailClient is a desktop application for sending and receiving emails via **SMTP** and **POP3**. It features **custom end-to-end encryption** based on a dynamic Base64 encoding table, ensuring that only the intended recipient can read the messages. This project is developed as part of the Computer Networks course at the School of Cyber Security, University of Chinese Academy of Sciences.

### Key Features
- ✉️ Send and receive emails using standard SMTP/POP3
- 🔒 End-to-end encryption for both message body and attachments
- 📇 Manage contact-specific encryption keys (communication table)
- ⚙️ Built-in support for popular email providers (QQ, 163, Gmail, etc.)
- ➕ Add custom mail server configurations
- 💻 Cross-platform GUI built with Flet (Windows, Linux)

### Built With

* [![Python][Python-badge]][Python-url]
* [![Flet][Flet-badge]][Flet-url]

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

- Python 3.10 or higher
- (Linux only) Install additional dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt install python3-tk libmpv2
  ```

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/your-username/MailClient.git
   ```
2. Install required packages
   ```sh
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## Usage

1. Navigate to the project folder
2. Run the application
   ```sh
   python app.py
   ```
3. Log in with your email address and password (any password works for local testing)
4. Use the interface to send/receive encrypted emails!

> **Note**: 
> For production use with real email services, ensure you enable "less secure apps" or generate an app-specific password if required by your provider.

## Compatibility

- ✅ Compatible with standard SMTP/POP3 email services (e.g., QQ Mail, 163 Mail, Gmail).
- ❌ **Not compatible** with ProtonMail or Tutanota due to their closed protocols and lack of standard POP3/SMTP support.


[Python-badge]: https://img.shields.io/badge/python-3776ab?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flet-badge]: https://img.shields.io/badge/Flet-00D1B2?style=for-the-badge&logo=flutter&logoColor=white
[Flet-url]: https://flet.dev/
