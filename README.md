# MiniGit (mgit)
Minimal reimplementation of Git, written in Python

## Overview
MiniGit is a CLI tool that implements core version control functionality. It mimics Git's filesystem structure, object formats, and internal protocols, making it partially Git-compatible. Some commits in this repository are created using mgit itself.

The project is written in modern, object-oriented Python with strong typing and a clean, class-based architecture. It relies exclusively on Python's built-in standard library.

This project is educational and was originally inspired by the [Write Yourself A Git](https://github.com/thblt/write-yourself-a-git) guide. While it provided the foundational logic for the Git format, MiniGit is a serious structural rewrite. The codebase has been refactored to move away from procedural scripts toward a scalable OOP architecture, fixing several edge-case bugs and implementing better patterns not found in the original tutorial.

## Screenshots
<img width="464" height="308" alt="Console screenshot" src="https://github.com/user-attachments/assets/8c7da133-df4a-4bf4-a3d9-32731b53cce2" />

## Features
MiniGit supports the following commands
| Command       | Description                                                     |
|--------------|-----------------------------------------------------------------|
| init         | Initialize an empty repository                                  |
| cat-file     | Display contents of an object                                   |
| hash-object  | Compute the hash of an object and optionally write it to the database |
| log          | Show history of a commit                                        |
| tag          | List and create tags                                            |
| ls-tree      | Print a tree object                                             |
| checkout     | Checkout a commit                                               |
| show-ref     | Show references                                                 |
| rev-parse    | Parse object identifiers                                        |
| ls-files     | List stage files                                                |
| check-ignore | Check paths against ignore rules                                |
| status       | Show the working tree status                                    |
| rm           | Remove files from the working tree and from the index           |
| add          | Add file contents to the index                                  |
| commit       | Record changes to the repository                                |

Note: Many commands implement core functionality only


## Technical stack

### Requirements
- Python 3.10+
  
### Optional requirements
- Shell (for tests)
  
## Usage
### Clone repository
```
git clone https://github.com/bokuyemskyy/mgit
cd mgit
```

### Setup
(Optional) Use virtual environment 
```
python3 -m venv .venv
source .venv/bin/activate
```

Install the tool
```
pip3 install -e .
```

### Run
After installation, the `mgit` command is available globally

Example:
```
mgit init
echo "Test" > 1.txt
mgit add .
mgit commit -m "initial commit"
```

## Credits
- Studies the official Git implementation and [documentation](https://git-scm.com/docs)
- Inspired by the [Write Yourself A Git](https://github.com/thblt/write-yourself-a-git) guide
