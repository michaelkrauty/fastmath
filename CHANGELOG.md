# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-04-07

### Added
- Smart problem selection system that considers:
  - Time taken to solve problems (adjusted for typing time)
  - Previous wrong/right answers for specific problems
  - Different problem orientations (e.g., 4+12 vs 12+4)
- Improved performance tracking with problem-specific metrics
- Enhanced difficulty adjustment based on individual problem performance

### Changed
- Problem generation algorithm now prioritizes problems that need more practice
- README updated with detailed feature descriptions
- Enhanced data storage to track more granular problem performance

### Fixed
- Improved handling of commutative operations (addition and multiplication)
- Better normalization of solution times based on answer complexity

## [1.0.0] - Initial Release

### Added
- Basic math practice with addition, subtraction, multiplication, and division
- Simple difficulty adjustment system
- Performance tracking by operation type
- Settings for enabling/disabling operations
- Manual difficulty controls