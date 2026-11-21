---
name: commit-message
description: Writes a commit message from the current changes. Use when the user asks for a commit message or asks how to describe their changes.
---

# Write a commit message

This skill is an example. The format below is only an example format; the team
replaces it with its real format.

## Steps

1. Look at the current changes (`git status`, `git diff`, and
   `git diff --staged` for staged changes).
2. Write a message in the following example format:

   ```text
   <area>: <imperative description>

   - Bullet point about one important change
   - Bullet point about another change
   ```

   A blank line separates the subject line from the bullet points.

3. Example:

   ```text
   docs: add guide for Remote-SSH

   - Add checklist for VS Code
   - Add note about skills in the home directory
   ```

## Important

Do not commit yourself. Only suggest the message and leave it to the user
whether and when to use it.
