# Contributing to DeskForge

Thank you for your interest in contributing to DeskForge! This guide will help you get started.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ (or SQLite for development)
- Redis 7+

### Backend Setup (API)
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
# Edit .env with your local settings
make dev
```

### Frontend Setup (Web)
```bash
cd apps/web
npm install
cp .env.local.example .env.local
# Edit .env.local with your local settings
npm run dev
```

### Running Tests
```bash
# Backend tests
cd apps/api
make test

# Frontend tests
cd apps/web
npm test
```

## First Change Walkthrough

1. **Fork & Clone** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the code style guide below
4. **Write tests** for new functionality
5. **Run the test suite** to ensure nothing is broken
6. **Commit** with a descriptive message: `git commit -m "feat: add your feature description"`
7. **Push** and create a Pull Request

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints for all function signatures
- Use `async/await` for all database operations
- Write docstrings for public functions
- Maximum line length: 100 characters

```python
async def get_tool(db: AsyncSession, tool_id: UUID, team_id: UUID) -> Tool:
    """Get a tool by ID and team."""
    result = await db.execute(
        sa.select(Tool).where(Tool.id == tool_id, Tool.team_id == team_id)
    )
    tool = result.scalar_one_or_none()
    if tool is None:
        raise ToolNotFoundError()
    return tool
```

### TypeScript (Frontend)
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use proper typing (avoid `any`)
- Follow the existing component patterns

```tsx
interface ToolCardProps {
  tool: Tool;
  onDelete?: (id: string) => void;
}

export function ToolCard({ tool, onDelete }: ToolCardProps) {
  // Component implementation
}
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting, missing semicolons, etc.
- `refactor:` code refactoring
- `test:` adding missing tests
- `chore:` maintenance tasks

## Pull Request Process

1. **Update documentation** if you changed APIs or added features
2. **Add tests** for new functionality
3. **Ensure CI passes** (linting, tests, type checking)
4. **Request review** from at least one maintainer
5. **Address feedback** promptly
6. **Squash commits** if requested before merge

### PR Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Project Structure

```
vulcan-1/src/
├── apps/
│   ├── api/          # FastAPI backend
│   │   ├── src/
│   │   │   ├── auth/       # Authentication & OAuth
│   │   │   ├── teams/      # Team management
│   │   │   ├── tools/      # Tool CRUD & generation
│   │   │   ├── datasources/# Data source connectors
│   │   │   ├── generate/   # AI generation pipeline
│   │   │   ├── billing/    # Stripe integration
│   │   │   └── models/     # SQLAlchemy models
│   │   └── tests/
│   └── web/          # Next.js frontend
│       └── src/
│           ├── app/        # Pages & routing
│           ├── components/ # React components
│           ├── hooks/      # Custom hooks
│           ├── stores/     # State management
│           └── lib/        # Utilities
```

## Need Help?

- Check the [documentation](https://hermes-agent.nousresearch.com/docs)
- Open an issue for bugs or feature requests
- Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the project's license.
