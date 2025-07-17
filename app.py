C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git push -u origin master
Enumerating objects: 2, done.
Counting objects: 100% (2/2), done.
Delta compression using up to 4 threads
Compressing objects: 100% (2/2), done.
Writing objects: 100% (2/2), 386 bytes | 128.00 KiB/s, done.
Total 2 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (1/1), done.
To https://github.com/lucianodiego/db.git
   efad735..4795fd5  master -> master
branch 'master' set up to track 'origin/master'.

C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git add .
warning: in the working copy of 'app.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'templates/index.html', LF will be replaced by CRLF the next time Git touches it

C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git commit -m "Feat: ripristina paginazione, ordinamento e layout"
[master d545a88] Feat: ripristina paginazione, ordinamento e layout
 2 files changed, 106 insertions(+), 32 deletions(-)

C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git push -u origin master
To https://github.com/lucianodiego/db.git
 ! [rejected]        master -> master (fetch first)
error: failed to push some refs to 'https://github.com/lucianodiego/db.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally. This is usually caused by another repository pushing to
hint: the same ref. If you want to integrate the remote changes, use
hint: 'git pull' before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.

C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git pull origin master
remote: Enumerating objects: 11, done.
remote: Counting objects: 100% (11/11), done.
remote: Compressing objects: 100% (6/6), done.
remote: Total 7 (delta 3), reused 0 (delta 0), pack-reused 0 (from 0)
Unpacking objects: 100% (7/7), 6.25 KiB | 25.00 KiB/s, done.
From https://github.com/lucianodiego/db
 * branch            master     -> FETCH_HEAD
   4795fd5..9204152  master     -> origin/master
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
Auto-merging templates/index.html
CONFLICT (content): Merge conflict in templates/index.html
Automatic merge failed; fix conflicts and then commit the result.

C:\Users\Diego\Downloads\cerca_persone\cerca_persone>git add .git commit -m "Feat: paginazione efficiente e ripristino UI"git push -u origin master
error: unknown switch `m'
usage: git add [<options>] [--] <pathspec>...

    -n, --[no-]dry-run    dry run
    -v, --[no-]verbose    be verbose

    -i, --[no-]interactive
                          interactive picking
    -p, --[no-]patch      select hunks interactively
    -e, --[no-]edit       edit current diff and apply
    -f, --[no-]force      allow adding otherwise ignored files
    -u, --[no-]update     update tracked files
    --[no-]renormalize    renormalize EOL of tracked files (implies -u)
    -N, --[no-]intent-to-add
                          record only the fact that the path will be added later
    -A, --[no-]all        add changes from all tracked and untracked files
    --[no-]ignore-removal ignore paths removed in the working tree (same as --no-all)
    --[no-]refresh        don't add, only refresh the index
    --[no-]ignore-errors  just skip files which cannot be added because of errors
    --[no-]ignore-missing check if - even missing - files are ignored in dry run
    --[no-]sparse         allow updating entries outside of the sparse-checkout cone
    --[no-]chmod (+|-)x   override the executable bit of the listed files
    --[no-]pathspec-from-file <file>
                          read pathspec from file
    --[no-]pathspec-file-nul
                          with --pathspec-from-file, pathspec elements are separated with NUL character


C:\Users\Diego\Downloads\cerca_persone\cerca_persone>