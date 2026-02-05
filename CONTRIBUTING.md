# Contributing to Nexus Sandbox

Thank you for your interest in contributing to the Nexus Global Payments Sandbox!

## 🚀 Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/nexus-sandbox.git`
3. **Install** dependencies:
   ```bash
   # Backend
   cd services/nexus-gateway
   pip install -e .
   
   # Frontend
   cd services/demo-dashboard
   npm install
   ```
4. **Start** the services: `docker compose up -d`

## 📋 Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, follow ESLint rules
- **Commits**: Use [Conventional Commits](https://conventionalcommits.org/)

```
feat: add new endpoint for quote locking
fix: correct pacs.008 XML parsing
docs: update API reference
test: add unit tests for FXP rates
```

### Branch Naming

- `feature/short-description`
- `fix/issue-number-description`
- `docs/what-changed`

## 🧪 Testing

```bash
# Backend tests
cd services/nexus-gateway
pytest --cov=src

# Frontend tests
cd services/demo-dashboard
npm run test
```

## 📝 Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add entries to CHANGELOG.md
4. Request review from maintainers

## 📚 Resources

- [Nexus Official Documentation](https://docs.nexusglobalpayments.org/)
- [ISO 20022 Message Catalogue](https://www.iso20022.org/)
- [Project ADRs](./docs/adr/)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Created by [Siva Subramanian](https://linkedin.com/in/sivasub987)
