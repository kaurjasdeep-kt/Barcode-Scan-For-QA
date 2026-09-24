**Barcode Generator — GitHub Pages Setup**



**What's been done**



**Built a client-side (JS-only)**



* index.html — same Code 128 / GS1-128 form and look as the Flask app
* bwip-js-min.js — barcode rendering library, bundled locally
* Runs entirely in the browser. No Python, no server, no data leaves the device.
* Validation/encoding logic (check digit, date parsing, payload building) ported from webapp.py and checked against it.
* Not yet done: opening index.html in an actual browser to click through it, and pushing anything to Git.



**What's left to do**



1\. Push the folder to a repo on Kroger GitHub Enterprise





* git init # skip if already a git repo
* git add docs/barcode-generator
* git commit -m "Add client-side barcode generator"
* git remote add origin <kroger-github-enterprise-repo-url>
* git push -u origin main



**2. Enable GitHub Pages**



Repo → Settings → Pages

Source: branch main, folder /docs (or the subfolder, if the org's GitHub Enterprise version supports picking a nested path)

Save — Pages generates a URL such as:



https://pages.<kroger-github-enterprise-host>/<org>/<repo>/



**3. Set who can view it**





Private repo → only invited collaborators/teams can open the page

Internal repo → anyone in the Kroger GitHub org can open it

Manage via Settings → Collaborators and teams



**4. How people use it once it's live**



Open the Pages URL in any browser (desktop or phone) — no install, no VPN beyond normal Kroger network/GitHub access

Pick barcode type, fill the form, click Generate, download the PNG



**5. Making future changes**



Edit index.html, commit, push — Pages redeploys automatically within a minute or two.

