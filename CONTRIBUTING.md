# Contributing Guide

Thank you for your interest in contributing to AI reStarter! 🎉

## 🚀 Getting Started

### Prerequisites

- **Rust**: 1.82 or higher
- **Cargo**: Included with Rust
- **Git**

[Install Rust & Cargo](https://www.rust-lang.org/tools/install)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/scottlz0310/AI_reStarter.git
   cd AI_reStarter
   ```

2. **Verify installation**
   ```bash
   cargo --version
   ```

3. **Build the project**
   ```bash
   cargo build
   ```

4. **Verify the setup**
   ```bash
   # Run tests
   cargo test

   # Run linting
   cargo clippy

   # Check formatting
   cargo fmt -- --check
   ```

## 🔄 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write your code following standard Rust conventions
- Add tests for new functionality in `tests/` or unit tests within modules
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in module"
git commit -m "docs: update README"
git commit -m "test: add unit tests for feature"
```

### 4. Push and Create PR

```bash
git push origin your-branch-name
```

Then create a Pull Request on GitHub.

## 📝 Code Style

### Rust Code Style

We use the standard Rust toolchain for code quality:

- **rustfmt**: For code formatting (standard configuration)
- **clippy**: For linting and common mistake detection

### Style Guidelines

- Follow standard Rust naming conventions (snake_case for functions/variables, CamelCase for types)
- Use `Result` and `Option` for error handling (avoid `unwrap()` in production code)
- Write documentation comments (`///`) for public functions and structs
- Keep code safe; avoid `unsafe` blocks unless absolutely necessary and documented

### Example

```rust
/// Processes input data and returns a result.
///
/// # Arguments
///
/// * `items` - A slice of strings to process
///
/// # Returns
///
/// A vector of processed strings, or an error if processing fails.
pub fn process_data(items: &[String]) -> Result<Vec<String>, String> {
    if items.is_empty() {
        return Err("Input is empty".to_string());
    }

    let processed: Vec<String> = items
        .iter()
        .map(|s| s.trim().to_lowercase())
        .collect();

    Ok(processed)
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name
```

### Writing Tests

- Place unit tests in a `tests` module within the same file:
  ```rust
  #[cfg(test)]
  mod tests {
      use super::*;

      #[test]
      fn test_process_data() {
          let input = vec!["  Hello  ".to_string()];
          let result = process_data(&input).unwrap();
          assert_eq!(result, vec!["hello".to_string()]);
      }
  }
  ```
- Place integration tests in the `tests/` directory.

## 📚 Documentation

### Doc Comments

Use `///` for documentation comments. These support Markdown.

```rust
/// Adds two numbers together.
///
/// # Examples
///
/// ```
/// let result = add(2, 2);
/// assert_eq!(result, 4);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

## 🔒 Security

### Security Guidelines

- Never commit secrets, API keys, or passwords.
- Use `cargo audit` to check dependencies for vulnerabilities (optional but recommended).

## 🐛 Bug Reports

When reporting bugs, please include:

- Rust version (`rustc --version`)
- Operating System (Windows version)
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs (`RUST_LOG=debug` output is helpful)

## ✨ Feature Requests

When requesting features:

- Describe the problem you're trying to solve
- Explain why this feature would be useful
- Consider if it fits the project's scope

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code compiles without warnings (`cargo check`)
- [ ] Code is formatted (`cargo fmt`)
- [ ] Tests pass (`cargo test`)
- [ ] Documentation is updated (`cargo doc` verifies doc tests)
- [ ] Commit messages follow conventional commits

## 🤝 Code Review Process

1. **Automated Checks**: CI will run `cargo test`, `clippy`, and `fmt`
2. **Peer Review**: Walk through the changes
3. **Merge**: Squash and merge into main

## 🏷️ Release Process

1. Update version in `Cargo.toml`
2. Update `CHANGELOG.md`
3. Create a release PR or Tag
4. CI will handle the build and release

## 💬 Getting Help

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and features

Thank you for contributing! 🎉
