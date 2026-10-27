# 07. Registering the approver

Date: 27 October 2026. Result: approver `manager-pavan`, key `manager-pavan-key-2`, registered as an approval issuer. Change id `f85a497a-139e-447a-94fb-e6ea01874f50`, status `APPROVED`.

This file records what was done, why each step exists, and how to repeat it. Labels follow `README.md`: **Observed** means it appeared in a command's output.

## 1. Why this step exists

A manager's approval is a signature. Parmana checks it with a public key. Parmana must be told which keys are trusted, or it refuses every approval. A key that is not registered is not trusted, even if its signatures are valid.

Registering a key is a production change. It decides who can approve refunds. So it needs two people in the normal process: one proposes, another approves. This is the step where a bad key would do the most damage.

## 2. Why the key was generated fresh

An existing pair from 11 October 2026 was found in two folders, `C:\Users\Pavan Charak\parmana-approver` and `D:\parmana-approver`. The two copies were identical, and the pair matched. Its origin could not be confirmed, so it was not used. The operator chose a fresh pair, so that every step of this key's history is known.

The old pair stays where it is. It is not registered, and it should be deleted once the new key is confirmed working.

## 3. The steps, with commands and outcomes

### 3.1 Generate the key pair (on the approver's machine)

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\parmana-approver-fresh" | Out-Null
npx tsx scripts/generate-approver-key.ts --approver-id manager-pavan --key-id manager-pavan-key-2 --out-dir "$env:USERPROFILE\parmana-approver-fresh"
```

**Why:** the generator writes an Ed25519 pair, and the folder must exist first (the generator does not create it).

**Observed:** the private key was written to `...\parmana-approver-fresh\manager-pavan__manager-pavan-key-2.private.pem`, and the public key to the matching `.public.pem`.

**Failed first:** `ENOENT` because the folder did not exist. Fixed by `New-Item` first.

### 3.2 Check the pair matches

```powershell
$n = "$env:USERPROFILE\parmana-approver-fresh\manager-pavan__manager-pavan-key-2"
node -e "const fs=require('fs'),c=require('crypto');const p=c.createPrivateKey(fs.readFileSync(process.argv[1]));const pub=c.createPublicKey(p).export({type:'spki',format:'pem'});console.log(p.asymmetricKeyType, pub.trim()===fs.readFileSync(process.argv[2],'utf8').trim()?'PAIR MATCHES':'PAIR DOES NOT MATCH')" "$n.private.pem" "$n.public.pem"
```

**Why:** the public key that gets registered must be the one derived from the private key. A mismatch would mean signatures that never verify.

**Observed:** `ed25519 PAIR MATCHES`. The check prints only the key type and the result. No key is displayed.

### 3.3 Get the helper that can register an approver

```powershell
git status --short
git fetch origin feat/approval-issuers-governance:feat/approval-issuers-governance
git switch feat/approval-issuers-governance
```

**Why:** the registration commands exist only on that branch (pull request #168). `main` did not have them.

**Failed first:** `git switch feat/approval-issuers-governance` returned `invalid reference`, because the branch had not been fetched on this machine. The fetch fixed it. The helper on `main` also failed with `The first argument must be one of: ... propose-revoke, approve.`, which lists no issuer commands.

**Observed:** `git status --short` was clean before the switch.

### 3.4 Load the maker's key (no typing, no clipboard)

```powershell
$env:PARMANA_URL = "https://parmana-api-real.vercel.app"
$dir = "C:\Users\Pavan Charak\parmana-secrets-fresh"
$g = "examples/live-checks/governance.ts"
function Use-KeyFile([string]$id) {
  $secure = Get-Content "$dir\$id.key.dpapi" | ConvertTo-SecureString
  $env:PARMANA_API_KEY = [System.Net.NetworkCredential]::new("", $secure).Password
  "  $id key loaded: $($env:PARMANA_API_KEY.Length) characters"
}
Use-KeyFile 'maker-pavan'
```

**Why:** the proposer must be a different caller from the approver. `maker-pavan` proposes; `pavancharak` approves.

**Observed:** `maker-pavan key loaded: 43 characters`.

### 3.5 Propose the approver (maker)

```powershell
npx tsx $g propose-issuer --approver-id manager-pavan --key-id manager-pavan-key-2 --public-key-file "$env:USERPROFILE\parmana-approver-fresh\manager-pavan__manager-pavan-key-2.public.pem" --reason "Approver for the live refund check."
```

**Why:** the proposal records the public key and the reason. It changes nothing yet. It is a pending change until a checker approves it.

**Observed:**

```
"changeId": "f85a497a-139e-447a-94fb-e6ea01874f50"
"action": "add", "approverId": "manager-pavan", "keyId": "manager-pavan-key-2"
"proposedBy": "maker-pavan", "status": "PENDING_APPROVAL"
Proposed: f85a497a-139e-447a-94fb-e6ea01874f50, PENDING_APPROVAL
```

**Failed first:** the same command on `main` printed the list of commands instead, because the helper had no issuer commands. Fixed by section 3.3.

### 3.6 Approve the approver (checker, step-up key)

```powershell
Use-KeyFile 'pavancharak'
npx tsx $g approve-issuer --id f85a497a-139e-447a-94fb-e6ea01874f50 --step-up-key-file "$dir\checker.step-up.private.pem" --step-up-key-id pavancharak
```

**Why:** the approval needs a step-up authorization, signed by the checker's own step-up key, for this change id and the action `approve`. The server refuses it if the proposer approves.

**Observed:** the script printed the pending change and waited. The operator typed `APPROVE` (exact word, case-sensitive). The output was `Status: APPROVED`.

**Note:** the proposer and the approver were the same person, `Pavan`, under two keys. The runbook's second-person review was not met. This was accepted for the test only, as recorded in `05`.

## 4. What the approval does

The approve route applies the change and resolves it in one step (`packages/api/src/routes/approval-issuers.ts`). The key becomes a trusted issuer, and signatures made with it are accepted for approvals.

## 5. How to check it is in force

Not yet run. Run it with the checker's key loaded:

```powershell
Invoke-RestMethod "$env:PARMANA_URL/approval-issuers/changes?status=APPROVED" -Headers @{ Authorization = "Bearer $env:PARMANA_API_KEY" }
```

**Expect:** the change `f85a497a-...` with `status` `APPROVED`, `approverId` `manager-pavan`, `keyId` `manager-pavan-key-2`.

## 6. Lessons

- Fetch a branch before trying to switch to it.
- The helper on `main` does not have issuer commands. Commands on a feature branch must be merged before they are relied on in production, or the operator has to use the branch.
- A proposal does nothing until approved, so it is safe to propose first and review.
- The approval is the production change. It took one command and one word, which is why the check of what is being approved matters: the printed change must match what was proposed.
- Keep the single-person deviation visible, and remove it when a real second approver exists.

## 7. What still needs doing

1. Run the check in section 5.
2. Use the approver's key to sign a real approval for the test payment (see `06`, step 5).
3. Run the approved refund through the MCP tool (see `06`, step 6).
4. Delete the 11 October pair after the new key is confirmed working.
