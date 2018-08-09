import re
import sys
from argparse import ArgumentParser

from git import Git, Repo, GitCommandError

'''
Дан Git репозиторий, с несколькими ветками: master, A, B, C.
A, B, C форкнуты из мастера и отличаются от него на несколько коммитов.

напишите программу, с простеньким cmd интерфейсом, которая принимает на вход название двух веток:
./my_programm <BRACH#1> <BRACH#2>
мержит со squash BRACH#1 в BRACH#2, если BRACH#1 уже была вмержена в BRACH#2, то merge commit удаляется(другие коммиты должны остаться) и мерж производится вновь.
'''


def merge(repo: Repo, source, target):
    git_cli: Git = repo.git
    git_cli.checkout(target)

    # we do "merge --squash" so we cannot determine merge commit by number of its parents
    # so lets determine by commit message (starts with Merged:{name})...
    # name of the source branch may be changed since last merge :(
    merge_commit_regexp = re.compile(rf'^Merged:{source}.*')
    for commit in repo.iter_commits(target, paths=source):

        if merge_commit_regexp.match(commit.message):
            onto_commit = next(commit.iter_parents()).hexsha
            from_commit = commit.hexsha
            git_cli.rebase('--onto', onto_commit, from_commit)
            break

    try:
        git_cli.merge(source, squash=True)

        if not repo.is_dirty():
            sys.exit(f'Cannot merge {source} into {target}. Branches are equal and they have never been merged before.')

        git_cli.commit('-m', f'Merged:{source}:{repo.heads[source].commit}')

    except GitCommandError as exc:

        git_cli.reset(hard=True)
        sys.exit(f'Command failed: {" ".join(exc.command)}\nReason:{exc.stderr or exc.stdout}')


if __name__ == "__main__":
    arg_parser = ArgumentParser(prog="Merger", description="Merge branches")
    arg_parser.add_argument('--git-path', dest='git_path', default='.', help="Path to git repo")
    arg_parser.add_argument('source', help="Source branch")
    arg_parser.add_argument('target', help="Target branch")

    args = arg_parser.parse_args()

    repo = Repo(args.git_path)

    merge(repo, args.source, args.target)
