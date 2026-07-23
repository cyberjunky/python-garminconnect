# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately by creating a [security advisory](https://github.com/cyberjunky/python-garminconnect/security/advisories) on GitHub.

**Please do NOT open a public issue for security vulnerabilities.** This allows us to address the issue before it becomes public knowledge.

## Security Considerations

### Credential Storage

python-garminconnect stores you login tokens in your home folder (depending on how the project has implemented it:

- Keep your `.garminconnect' folder secure
- Do not share your home folder backups without sanitizing sensitive data

### Best Practices

1. **Keep library updated** - Security patches are released regularly
2. **Install from official sources** - Use the official PyPi releases
3. **Review the code** - As an open-source project, you can audit the code before use
4. **Secure your network** - Restrict access to your home folder
5. **Use strong authentication** - Enable Garmin Connects MFA authentication

## Disclosure Timeline

When a vulnerability is confirmed:

1. We will assess the severity and impact
2. A fix will be prepared for the latest version
3. A new release will be published
4. A security advisory will be published on GitHub (with credit to the reporter if desired)

Thank you for helping keep this project secure!
