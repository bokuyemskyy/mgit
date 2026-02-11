#!/usr/bin/env bash

# These tests are directly taken from the original WYAG

set -e

function step() {
    pos=$(caller)
    echo $pos $@
}

mgit=$(which mgit)

testdir=/tmp/mgit-tests
if [[ -e $testdir ]]; then
    rm -rf $testdir/*
else
    mkdir $testdir
fi
cd $testdir
step "working on $(pwd)"

step Create repos
"$mgit" init left
git init right > /dev/null

step status
cd left
git status > /dev/null
cd ../right
git status > /dev/null
cd ..

step hash-object
echo "Don't read me" > README
"$mgit" hash-object README > hash1
git hash-object README > hash2
cmp --quiet hash1 hash2

step hash-object -w
cd left
"$mgit" hash-object -w ../README > /dev/null
cd ../right
git hash-object -w ../README > /dev/null
cd ..
ls left/.git/objects/b1/7df541639ec7814a9ad274e177d9f8da1eb951 > /dev/null
ls right/.git/objects/b1/7df541639ec7814a9ad274e177d9f8da1eb951 > /dev/null

step cat-file
cd left
"$mgit" cat-file blob b17d > ../file1
cd ../right
git cat-file blob b17d > ../file2
cd ..
cmp file1 file2

step cat-file with long hash
cd left
"$mgit" cat-file blob b17df541639ec7814a9ad274e177d9f8da1eb951 > ../file1
cd ../right
git cat-file blob b17df541639ec7814a9ad274e177d9f8da1eb951 > ../file2
cd ..
cmp file1 file2

step "Create commit (git only, nothing is tested)" 
cd left
echo "Aleph" > hebraic-letter.txt
git add hebraic-letter.txt
GIT_AUTHOR_DATE="2010-01-01 01:02:03 +0100" \
               GIT_AUTHOR_NAME="mgit-tests.sh" \
               GIT_AUTHOR_EMAIL="mgit@example.com" \
               GIT_COMMITTER_DATE="2010-01-01 01:02:03 +0100" \
               GIT_COMMITTER_NAME="mgit-tests.sh" \
               GIT_COMMITTER_EMAIL="mgit@example.com" \
               git commit --no-gpg-sign -m "Initial commit" > /dev/null
cd ../right
echo "Aleph" > hebraic-letter.txt
git add hebraic-letter.txt
GIT_AUTHOR_DATE="2010-01-01 01:02:03 +0100" \
               GIT_AUTHOR_NAME="mgit-tests.sh" \
               GIT_AUTHOR_EMAIL="mgit@example.com" \
               GIT_COMMITTER_DATE="2010-01-01 01:02:03 +0100" \
               GIT_COMMITTER_NAME="mgit-tests.sh" \
               GIT_COMMITTER_EMAIL="mgit@example.com" \
               git commit --no-gpg-sign -m "Initial commit" > /dev/null

cd ..

step cat-file on commit object without indirection
cd left
"$mgit" cat-file commit HEAD > ../file1
cd ../right
git cat-file commit HEAD > ../file2
cd ..
cmp file1 file2

step cat-file on tree object redirected from commit
cd left
"$mgit" cat-file tree HEAD > ../file1
cd ../right
git cat-file tree HEAD > ../file2
cd ..
cmp file1 file2

step "Add some directories and commits (git only, nothing is tested)"
cd left
mkdir a
echo "Alpha" > a/greek_letters
mkdir b
echo "Hamza" > a/arabic_letters
git add a/*
GIT_AUTHOR_DATE="2010-01-01 01:02:03 +0100" \
               GIT_AUTHOR_NAME="mgit-tests.sh" \
               GIT_AUTHOR_EMAIL="mgit@example.com" \
               GIT_COMMITTER_DATE="2010-01-01 01:02:03 +0100" \
               GIT_COMMITTER_NAME="mgit-tests.sh" \
               GIT_COMMITTER_EMAIL="mgit@example.com" \
               git commit --no-gpg-sign -m "Commit 2" > /dev/null
cd ../right
mkdir a
echo "Alpha" > a/greek_letters
mkdir b
echo "Hamza" > a/arabic_letters
git add a/*
GIT_AUTHOR_DATE="2010-01-01 01:02:03 +0100" \
               GIT_AUTHOR_NAME="mgit-tests.sh" \
               GIT_AUTHOR_EMAIL="mgit@example.com" \
               GIT_COMMITTER_DATE="2010-01-01 01:02:03 +0100" \
               GIT_COMMITTER_NAME="mgit-tests.sh" \
               GIT_COMMITTER_EMAIL="mgit@example.com" \
               git commit --no-gpg-sign -m "Commit 2" > /dev/null
cd ..

step ls-tree
cd left
"$mgit" ls-tree HEAD > ../file1
cd ../right
git ls-tree HEAD > ../file2
cd ..
cmp file1 file2

step checkout

cd left
"$mgit" checkout HEAD ../temp1
mkdir ../temp2
cd  ../temp2
git --git-dir=../right/.git checkout .
cd ..
diff -r temp1 temp2
rm -rf temp1 temp2

step rev-parse
cd left
"$mgit" rev-parse HEAD  > ../file1
"$mgit" rev-parse 8a617  >> ../file1

cd ../right
git rev-parse HEAD   > ../file2
git rev-parse 8a617  >> ../file2
cd ..
cmp file1 file2

step "ls-files "
cd left
"$mgit" ls-files > ../file1
cd ../right
git ls-files > ../file2
cd ..
cmp file1 file2

gitignore_prepare() {
    mkdir -p a/b/c/
    echo "!*.txt" > a/b/c/.gitignore
    echo "*.txt" > a/b/.gitignore
    echo "*.org" > a/.gitignore
    git add -A
}

step "gitignore"
cd left
gitignore_prepare
"$mgit" check-ignore a/b/c/hello.txt > ../file1
"$mgit" check-ignore a/b/hello.txt >> ../file1
"$mgit" check-ignore a/hello.org >> ../file1
"$mgit" check-ignore hello.org >> ../file1
cd ../right
set +e 
gitignore_prepare
git check-ignore a/b/c/hello.txt > ../file2
git check-ignore a/b/hello.txt >> ../file2
git check-ignore a/hello.org >> ../file2
git check-ignore hello.org >> ../file2
set -e
cd ..
cmp file1 file2


step "SUCCESS"