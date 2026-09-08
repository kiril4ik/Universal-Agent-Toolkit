# .NET Rules
- Follow target framework/C# version and existing analyzer/nullable settings.
- Prefer async all the way for I/O; pass cancellation tokens through external operations.
- Use DI/options/logging primitives consistently.
- Keep authorization server-side and validate external DTOs.
- Dispose resources correctly and run format/analyzers/tests.
