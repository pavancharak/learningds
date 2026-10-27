# 03. Incidents and fixes

Each entry: what was seen, why it happened, what fixed it, and what to do next time. Outcomes are quoted from the session.

## 1. Production API down: `PARMANA_API_KEYS is not valid JSON`

- **Seen:** `500 FUNCTION_INVOCATION_FAILED` on every request to `parmana-api-real`. The Runtime Logs (Error filter) said `PARMANA_API_KEYS is not valid JSON. Expected an array`.
- **Cause:** the value uploaded to Vercel was not the one-line JSON array the local file held. It was piped through PowerShell into `vercel env add`, which stored it mangled. The local file was valid, and `parseApiKeys` passed.
- **Fix:**
  1. Promote the last good deployment, `parmana-api-real-7j3nq8600`. Service returned `401`.
  2. Re-upload the list from a file with a redirect: `cmd /c "vercel env add ... < file"`.
  3. Redeploy and check `/policies`.
- **Next time:** never pipe a JSON string into `vercel env add`. Use the file redirect. Check `parseApiKeys` on the file before the upload.

## 2. A deployment went live while broken

- **Seen:** `vercel redeploy` reported `Ready` and aliased the new deployment to production. It was failing at startup.
- **Cause:** Vercel marks a build Ready when it builds, not when it starts. A bad environment value only shows at runtime.
- **Fix:** promote the last good deployment, as in incident 1.
- **Next time:** after every redeploy, run the `/policies` check immediately. Keep the last good deployment's URL in a note.

## 3. `env rm` ran without a matching `env add`

- **Seen:** after one failed `env add`, the variable was missing in production. A later redeploy would have failed.
- **Cause:** the `rm` step ran by itself, and the `add` step failed.
- **Fix:** run `env add` again, then redeploy.
- **Next time:** run `rm` and `add` back to back, and check `vercel env ls production` before any redeploy.

## 4. A hash check that passed when it should fail

- **Seen:** `MATCHES` for all four callers, from the in-session variables.
- **Cause:** `$live` and `$global:Keys` were empty. Both `$h` and `$e.keyHash` were `$null`, so they compared equal.
- **Fix:** rebuilt the check to fail on an empty side (`if ($e -and $h -eq $e.keyHash)`), and to read the list from the file.
- **Next time:** check the length of every value before comparing it. A match with empty inputs is not a match.

## 5. Pasted lines answered the key prompts

- **Seen:** a block with `Read-Host` prompts was pasted in full. The prompts took the pasted lines as their answers, so the keys were never confirmed as saved, and some entries were not written.
- **Fix:** cleared the fresh folder and regenerated the keys, one block at a time, pressing Enter only after saving each key.
- **Next time:** run one key block per paste. Wait for the prompt before pasting the next.

## 6. Variables lost between windows

- **Seen:** `$token`, `$dir`, `$link`, `$body` and `$env:PARMANA_URL` were empty in a new window. One request went out with an empty token and returned `401`. Another printed nothing because the URL was empty.
- **Fix:** set each variable in the same window, and check its length before a request.
- **Next time:** start each session with the block of variable definitions from `02`, section A.

## 7. `--cwd` with a space in the path

- **Seen:** `ENOENT: no such file or directory, chdir 'D:\last\parmana-core' -> 'C:\Users\Pavan'`.
- **Cause:** inside `cmd /c "..."` the path `C:\Users\Pavan Charak\...` was not quoted, so it split at the space.
- **Fix:** `Push-Location $link`, then run the command without `--cwd`, using a quoted redirect.
- **Next time:** use `Push-Location` for any folder with a space in its path.

## 8. Plain-text key files in the secrets folder

- **Seen:** `maker-pavan.key.txt`, `pavancharak.key.txt`, `kill-switch-probe.key.txt`, plus a `pasted` key from chat.
- **Cause:** earlier steps saved keys as text files. The rotation was meant to remove them.
- **Fix:** keys now sit in the password manager, and as encrypted `*.key.dpapi` files that decrypt only for the Windows account. The old text files were deleted.
- **Next time:** never write a raw key to a file. Write it with `ConvertFrom-SecureString`, and keep the password-manager copy.

## 9. `PARMANA_URL` empty, and a silent failure

- **Seen:** `curl.exe -s "$env:PARMANA_URL/policies"` printed nothing. `"[$env:PARMANA_URL]"` printed `[]`.
- **Cause:** the variable was not set in that window. The URL became `/policies`, which curl could not resolve, and `-s` hid the error.
- **Fix:** set the URL, then run without `-s`.
- **Next time:** a blank response is not a result. Check the variable first, then drop `-s` to see errors.

## 10. Keys pasted into chat

- **Seen:** operator keys were typed at a `Read-Host` prompt in a window whose transcript was shared with the assistant.
- **Fix:** both keys were rotated, the new list uploaded, and the old keys rejected.
- **Next time:** prompts that take keys should be used only in a window that is not shared. Use `Read-Host -AsSecureString` and never echo the value.

## 11. The kill switch was on

- **Seen:** the refusal test returned `500` with `KILL_SWITCH_ACTIVE` in the logs. Status showed `active true`, version 1, tripped by `operator-a`, reason `probe`.
- **Cause:** a trip recorded earlier (before the rotation). Nobody had reset it. The trip label `operator-a` was not in the current caller list.
- **Fix:** the operator confirmed the trip was a mistake. `maker-pavan` started a reset (`202`, pending), and `pavancharak` completed it (`200`, reset). Status: `active false`, version 3.
- **Next time:** a trip needs a written cause. Two operators must reset it, and the reset reasons should say what was checked. The reasons `mistake` and `ok` were not enough.

## 12. Two operators on one machine

- **Seen:** both operator keys were used from the same machine by the same person.
- **Cause:** the test had one operator. The guide asks for two different people.
- **Fix:** recorded in the journey, and the founder should decide whether this is acceptable. Not repeated for production.
- **Next time:** a second person completes the reset from their own machine.

## 13. Git set up in the wrong folder

- **Seen:** `git init` ran in `D:\last\parmana-agent-studio-mcp`, the Vercel build output.
- **Cause:** the command ran in the build folder by mistake.
- **Fix:** the repository was removed from that folder, and a new one was created at `D:\last\learningds`.
- **Next time:** check the folder with `Get-Location` before `git init`.

## 14. The remote was added with a placeholder

- **Seen:** `git remote add origin https://github.com/<owner>/learningds.git`, with the literal `<owner>`.
- **Fix:** `git remote set-url origin https://github.com/pavancharak/learningds.git`.
- **Next time:** never run a command that still contains `<...>`.

## 15. A partial code change left on a branch

- **Seen:** a change to `governance.ts` was started on `feat/approval-issuers-governance` to add approval-issuer support. It was not finished.
- **Fix:** the file was reverted with `git checkout --`, so the branch is clean.
- **Next time:** finish a change before saving it. Do not leave a half-edited file in a branch that someone else might pick up.

## 16. The approver key does not exist

- **Seen:** `NO DOES NOT EXIST` for the demo's `manager-pavan` approver key.
- **Cause:** the demo was run on a different machine, and its approver key was never created here. An approver must also be registered as an approval issuer, or its signature is not trusted.
- **Fix:** open. See `05-grant-and-approval.md`.
