argsp = argsubparsers.add_parser("ls-tree", help="Print a tree object")
argsp.add_argument(
    "-r", dest="recursive", action="store_true", help="Recurse into sub-trees"
)
