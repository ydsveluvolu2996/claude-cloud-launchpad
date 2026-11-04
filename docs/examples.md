# Three things to try

These are guided examples, not transcripts from authenticated service tests. The example results below illustrate the kind of answer to look for; Claude's wording and live prices will vary.

First complete the [installation guide](../README.md) and run the checker for your profile. Open Claude in a practice folder using Terminal on macOS or Git Bash on Windows:

```bash
mkdir -p "$HOME/claude-practice"
cd "$HOME/claude-practice"
claude
```

Paste the prompts **inside Claude Code**. Review any request to run a tool before approving it. These exercises do not need your AWS credentials and do not ask Claude to create infrastructure.

## 1. Plan a small website's AWS costs

**Use:** AWS or Full profile, with the pricing connector connected. You need Node.js and `npx`; the default calculator workflow does not require AWS credentials.

**Prompt**

> Use AWS Pricing Calculator to plan a small static website in us-east-1. Assume 1 GB of stored files and 10,000 page visits per month. Ask me about average page size, requests per visit, and CDN use before estimating. Show each assumption, monthly line item, and what the estimate excludes. Do not access my AWS account, deploy resources, or create any infrastructure.

**What should happen**

Claude should ask for missing usage assumptions rather than presenting a precise total immediately. After you answer, it can use the calculator to build an estimate. Check the service, region, request counts, data transfer, and currency before relying on it.

**Illustrative result format — not a live price quote**

| Part of the estimate | What the answer should explain |
|---|---|
| Storage | Amount stored and the pricing basis used |
| Requests | Visits multiplied by the agreed requests per visit |
| Delivery | Assumed page size, data transfer, and CDN choice |
| Monthly total | Calculated from those assumptions, with a source or estimate link when available |
| Exclusions | Items such as domains, taxes, or services not included |

If it offers to deploy the website, remind it that this exercise is only an estimate. Creating a calculator estimate is separate from creating AWS resources.

## 2. Understand a Terraform configuration

**Use:** AWS or Full profile. To use the Terraform documentation connector, install and start Docker as described in [service setup](../README.md#connect-the-tools-you-need). This reading exercise does not need Terraform account credentials or AWS credentials.

**Prompt**

```text
Use the Terraform plugin's documentation tools to explain the configuration
below to a beginner. Describe what each block means and identify what I
should decide before using it. Do not run terraform init, plan, or apply,
and do not access any cloud account.

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "launchpad-example-not-for-deployment"
}
```

**What should happen**

The answer should explain the provider, region, resource type, local Terraform label, and bucket name. It should distinguish reading configuration from applying it.

**Illustrative result**

> The provider tells Terraform which service it would talk to and which region to use. `aws_s3_bucket` declares the kind of resource, while `example` is the label used inside the Terraform configuration. Before deployment, you would need to choose a suitable bucket name and review access, encryption, lifecycle, and cost requirements. Nothing has been created by this explanation.

Ask a follow-up such as: “Explain Terraform state using a simple analogy.” If the documentation connector is unavailable, check Docker and `/mcp`; Claude can still explain pasted text, but that would not validate the connector.

## 3. Improve a signup page with the design plugin

**Use:** Collaboration or Full profile. Pasted text needs no Figma, Slack, or GitHub account connection.

**Prompt**

> Use the design plugin to review this signup-page copy for clarity and accessibility. Give three specific improvements, explain why each helps, and suggest revised text. Use only the text I paste; do not connect to external accounts.
>
> Heading: Unlock next-generation productivity
> Description: Our platform empowers you to achieve more.
> Button: Submit
> Error: Invalid input

**What should happen**

Look for concrete suggestions that explain the product, make the button's action clear, and help someone recover from an error. Claude should ask what the product actually does if that information is missing.

**Illustrative result**

| Current copy | Useful direction |
|---|---|
| “Unlock next-generation productivity” | Replace this with the actual task the product helps people complete |
| “Submit” | Name the action, such as “Create account,” if that is what the button does |
| “Invalid input” | Identify the field and explain how to correct it, such as “Enter an email address in the format name@example.com” |

These suggestions demonstrate text review. Testing keyboard navigation, contrast, and screen-reader behavior requires the actual interface and separate checks.

## If an example stops working

Type `/exit`, return to the Launchpad folder, and run `bash doctor.sh` with your chosen `--profile`. Then check the relevant connector in `/mcp`. See [Troubleshooting](../README.md#troubleshooting) or [open a sanitized bug report](https://github.com/ydsveluvolu2996/claude-cloud-launchpad/issues/new?template=bug_report.yml).
