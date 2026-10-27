# 02. Commands and outcomes

Each block shows a command as it was run (with values that are secret removed), and the outcome that was printed. Replacements are marked `<...>`. Identifiers that are not secret are kept.

Run from `D:\last\parmana-core` unless a block says otherwise.

## A. Setting up a session

```powershell
$env:PARMANA_URL = "https://parmana-api-real.vercel.app"
$dir = "C:\Users\Pavan Charak\parmana-secrets-fresh"
$g = "examples/live-checks/governance.ts"
```

**Outcome:** variables set. Lesson: they do not survive a new window. A later check printed `[]` for `PARMANA_URL`, which made a request go to a relative path and print nothing (see `03`, incident 9).

## B. Checking the API

```powershell
try { Invoke-RestMethod "$env:PARMANA_URL/policies" } catch { "$($_.Exception.Response.StatusCode.value__) $($_.ErrorDetails.Message)" }
```

**Outcomes seen:**

- `401 {"error":"authentication required"}`: healthy. The API is up and checking keys.
- `500 FUNCTION_INVOCATION_FAILED`: startup is failing. The deployment cannot serve requests.
- A blank line with no error: the URL was empty (`PARMANA_URL` unset). Not a real result.

```powershell
curl.exe -i https://parmana-api-real.vercel.app/policies
```

**Outcome:** `HTTP/1.1 401 Unauthorized`, `Www-Authenticate: Bearer realm="Parmana"`, body `{"error":"authentication required"}`. This confirmed the route and the API were healthy when `PARMANA_URL` was empty in the window.

## C. Reading the production error

```powershell
npx vercel logs parmana-agent-studio-mcp.vercel.app --since 10m --json
```

**Outcome:** a log line with `"message":"{\"event\":\"mcp_error\",\"message\":\"authentication required\"}"` and `responseStatusCode: 500`. The MCP server had called Parmana with a key Parmana did not recognise.

```powershell
vercel logs parmana-agent-studio-mcp.vercel.app --since 10m
```

**Outcome:** the plain output cut the message off at `au…`. Use `--json` to see the full text.

Parmana's Runtime Logs (dashboard): `injected env (0) from ../../.env Error: PARMANA_API_KEYS is not valid JSON. Expected an array...`

## D. The kill switch

```powershell
$nonce = "check-$(Get-Date -Format yyyyMMdd-HHmm)"
curl.exe -s "$env:PARMANA_URL/kill-switch/status?nonce=$nonce" -H "Authorization: Bearer $k"
```

**Outcome:** `{"active":true,"version":1,"trippedBy":"operator-a","trippedAt":"2026-10-27T10:06:39.336Z","tripReason":"probe",...}`.

Reset, first request, by `maker-pavan`:

```powershell
curl.exe -s -X POST "$env:PARMANA_URL/kill-switch/reset" -H "Authorization: Bearer <maker key>" -H "Content-Type: application/json" -d "{\`"reason\`":\`"$reason\`"}"
```

**Outcome:** `{"outcome":"pending","state":{"active":true,"version":2,...,"pendingResetBy":"maker-pavan","pendingResetReason":"mistake"}}`.

Reset, second request, by `pavancharak`:

**Outcome:** `{"outcome":"reset","state":{"active":false,"version":3,...,"resetRequestedBy":"maker-pavan","resetBy":"pavancharak","resetReason":"ok"}}`.

Lesson: the reasons `mistake` and `ok` are too thin for the incident log. The guide asks for the cause and what was checked. (See `03`, incident 12.)

## E. The refusal test

```powershell
$body = '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"propose_refund","arguments":{"paymentId":"pay_TrPtgJ3RVnzzFi","amountPaise":100}}}'
Invoke-RestMethod -Uri https://parmana-agent-studio-mcp.vercel.app/api/mcp -Method Post -Headers @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" } -Body $body | ConvertTo-Json -Depth 10
```

**Outcomes, in order:**

- `401 Unauthorized`: the bearer token was empty or wrong.
- `500 Internal Server Error`, log `authentication required`: the agent's key was not in Parmana's live list.
- `500 Internal Server Error`, log `KILL_SWITCH_ACTIVE`: after the key was fixed, the kill switch was still on. Parmana refused every request until it was reset.
- `REFUSED`, `rule: authority-not-authorized`, `businessTransactionId: 89ce368c-eb76-467e-af73-d74480b1698a`. Reason: `"razorpay-refund-agent" holds no authority grant for "razorpay:refund".` This was the first success.
- `REFUSED`, same rule, `businessTransactionId: ec54373f-e824-4342-9716-4e1e0936ec3f`. This was after the MCP token and agent key were rotated.

## F. Checking a key against its entry

```powershell
$h = node -e "console.log(require('crypto').createHash('sha256').update(process.argv[1]).digest('hex'))" $typed
if ($h -eq $e.keyHash) { "$id : MATCHES" } else { "$id : DOES NOT MATCH" }
```

**Outcomes:**

- `MATCHES` for all four, from the in-session variables. **Invalid:** the variables were empty, so both sides were `$null` and compared equal. Fixed in `03`, incident 4.
- `pavancharak : DOES NOT MATCH` for a key typed from the password manager. That key came from an interrupted run and was never a valid copy.
- `MATCHES` for all four after the clean regeneration, from the encrypted `*.key.dpapi` files.

## G. Uploading the caller list

```powershell
Push-Location $link
vercel env rm PARMANA_API_KEYS production --yes
cmd /c "vercel env add PARMANA_API_KEYS production --sensitive < `"$dir\PARMANA_API_KEYS.json`""
Pop-Location
```

**Outcomes:** `Removed Environment Variable`, then `✓ Added PARMANA_API_KEYS`, Environments: Production.

The first attempt, which piped the value through PowerShell, was stored incorrectly (see `03`, incident 1). The file redirect worked.

```powershell
vercel redeploy https://parmana-api-real-<deployment>.vercel.app --target production --cwd $link
```

**Outcomes:** `✓ Ready` for the new deployment, and `Aliased https://parmana-api-real.vercel.app`. Several redeploys printed `Error: fetch failed` after creating the deployment. The deployment still existed and was checked with `vercel inspect` (Ready). Do not treat `fetch failed` as a failed deploy; check the status.

Latest production deployments in this sequence: `parmana-api-real-k2p4fmsfl` (rotation 2), `parmana-api-real-od2ekipnr` (fresh list, 27 October, evening).

## H. The MCP project

```powershell
cd D:\last\parmana-agent-studio-mcp
$secure = Get-Content "$dir\razorpay-refund-agent.key.dpapi" | ConvertTo-SecureString
$plain = [System.Net.NetworkCredential]::new("", $secure).Password
npx vercel env rm PARMANA_API_KEY production --yes
$plain | npx vercel env add PARMANA_API_KEY production --sensitive
Remove-Variable plain
npx vercel deploy --prod --yes
```

**Outcomes:** `Removed`, `Added PARMANA_API_KEY`, and `Ready` for `parmana-agent-studio-k0ngd6jl5`.

New MCP token:

```powershell
$newTok = -join ((48..57 + 65..90 + 97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
```

**Outcome:** a 48-character token. It was saved in the password manager and as `agent-studio-token.dpapi`. The old file held a 43-character value, which the server rejected.

## I. The caller list rebuilt from entries

```powershell
$all = @(
  (Get-Content "$dir\pavancharak-entry.json" -Raw | ConvertFrom-Json),
  (Get-Content "$dir\maker-pavan-entry.json" -Raw | ConvertFrom-Json),
  (Get-Content "$dir\kill-switch-probe-entry.json" -Raw | ConvertFrom-Json),
  (Get-Content "$dir\razorpay-refund-agent-entry.json" -Raw | ConvertFrom-Json)
)
[System.IO.File]::WriteAllText("$dir\PARMANA_API_KEYS.json", (ConvertTo-Json -InputObject $all -Depth 6 -Compress))
npx tsx -e "import { parseApiKeys } from './packages/shared/src/config/ConfigValidation.ts'; console.log('OK', parseApiKeys(process.env.KEYS).map(e => e.callerId))"
```

**Outcome:** `OK` with the four caller ids. This check is run before every upload.

## J. Generating a caller key

```powershell
$out = npx tsx scripts/generate-api-key.ts --caller-id razorpay-refund-agent --credential-holder-type SERVICE --allowed-capabilities "razorpay:refund"
```

**Outcome:** `key length: 43`. The raw key is printed once. It was saved to the password manager at the prompt. Its entry JSON was written to the fresh folder.

## K. Encrypting keys to the Windows account

```powershell
ConvertTo-SecureString $_.Value -AsPlainText -Force | ConvertFrom-SecureString | Set-Content "$dir\$($_.Key).key.dpapi"
```

**Outcome:** four `*.key.dpapi` files, each 622 bytes. They decrypt only for the same Windows account. Checked with the hash comparison in section F: `MATCHES` for all four.

## L. The GitHub secrets

- `PARMANA_PROBE_KEY` was updated with the probe key, from `kill-switch-probe.key.dpapi` through the clipboard. GitHub showed `Secret updated`.
- `PARMANA_API_KEYS` (repository secret) was deleted. No workflow read it.
- The probe workflow was run from the Actions tab. **Outcome:** green.

## M. The learning repository

```bash
git clone --depth 1 https://github.com/pavancharak/learningds /home/user/learningds
git -c user.name="Pavan Dev Singh Charak" -c user.email="charak1987@gmail.com" commit -q -s --author="..." -m "..."
git push -q origin HEAD:main
```

**Outcomes:** commits `1fcdc4d` (starter), `eaa8a78` (this journey document), `7ac9582` (README). Each carries a `Signed-off-by` line.

Lesson: `git init` was first run in the wrong folder (the MCP build output), and `git remote add` was first given the literal `<owner>`. Both were corrected (see `03`).

## N. The authority grant

```powershell
Use-KeyFile 'maker-pavan'
npx tsx $g propose-grant --caller-id razorpay-refund-agent --capability razorpay:refund --max-amount 500 --valid-days 7
```

**Outcome:**

```
"changeId": "dbdd05f1-dac6-4477-86f3-4fa4ca528e82"
"callerId": "razorpay-refund-agent", "capability": "razorpay:refund"
"limits": { "parameters.amount": { "max": 500 } }
"validUntil": "2026-11-03T18:43:24.396Z"
"proposedBy": "maker-pavan", "status": "PENDING_APPROVAL"
```

```powershell
Use-KeyFile 'pavancharak'
npx tsx $g approve --kind grant --id $gid --step-up-key-file "$dir\checker.step-up.private.pem" --step-up-key-id pavancharak
```

**Outcomes, in order:**

- First run: `Type APPROVE ... approve` (typed the word `approve` in lower case, the helper stopped). `Stopped. Nothing was approved.`
- Second run: typed `APPROVE`. **Outcome:** `Status: APPROVED`.

Lesson: the approval wants exactly `APPROVE`. Anything else stops it safely.

## O. Approver key

```powershell
Test-Path "$env:USERPROFILE\parmana-approver\manager-pavan__manager-pavan-key-1.private.pem"
```

**Outcome:** `NO DOES NOT EXIST`. The demo's approver key was never created on this machine.

## P. The governance helper

```bash
git -C /home/user/parmana-core checkout -- examples/live-checks/governance.ts
```

**Outcome:** a partial edit to add approval-issuer support was reverted, so the branch is clean. Nothing was committed to `parmana-core` in this step.
