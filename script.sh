# #!/bin/bash

# # =============================
# # ⚙️  Update Specific Git Commits
# # =============================

# # New author details
# NEW_NAME="seanmanningcloud"
# NEW_EMAIL="seanmanningcloud@gmail.com"

# # List of commit hashes to update (space-separated)
# COMMITS=("a58e44bfa1c26c420bec65633b80d330dbc9b9e6" "60934701f0f9ba3d1074ea28cc4f019ec75e835f" "f0e4a18266e9a6e19928d82662732d241838b5ec", "a2654456a950c243bfc022771f422855acc8d1aa", "c9a86608633c1109ddb33a13f2bd85d67eee5c99")

# echo "🔄 Rewriting only selected commits..."
# echo "    New Name: $NEW_NAME"
# echo "    New Email: $NEW_EMAIL"
# echo ""

# git filter-branch --env-filter '
# NEW_NAME="'"$NEW_NAME"'"
# NEW_EMAIL="'"$NEW_EMAIL"'"

# COMMITS=("'"${COMMITS[@]}"'")

# for commit in "${COMMITS[@]}"; do
#     if [ "$GIT_COMMIT" = "$commit" ]; then
#         echo "✔️ Updating commit $commit"
#         export GIT_AUTHOR_NAME="$NEW_NAME"
#         export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
#         export GIT_COMMITTER_NAME="$NEW_NAME"
#         export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
#     fi
# done
# ' --tag-name-filter cat -- --all

# echo ""
# echo "✔️ Done! Verify using: git log --pretty=full"
# echo ""
# echo "⚠️ Don't forget to force push:"
# echo "   git push --force --tags origin <branch-name>"


export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --env-filter '
case "$GIT_COMMIT" in
    "4f3631cad79186194c7429bd007deba01d61282b")
        export GIT_AUTHOR_NAME="seanmanningcloud"
        export GIT_AUTHOR_EMAIL="seanmanningcloud@gmail.com"
        export GIT_COMMITTER_NAME="seanmanningcloud"
        export GIT_COMMITTER_EMAIL="seanmanningcloud@gmail.com"
        ;;
esac
' --tag-name-filter cat -- --all