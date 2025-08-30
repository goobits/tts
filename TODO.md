# TTS Development TODO

## Git Repository Cleanup (August 2025) ✅ COMPLETED

**⚠️ Important Historical Note**: This repository previously had git tracking issues where virtual environments and cache files were accidentally committed. These issues have been resolved:

- **✅ Removed 3,849 venv/ files** from git tracking (virtual environment should never be committed)
- **✅ Removed 29 cache/temp files** (.cache/ and .temp/ directories) 
- **✅ Updated .gitignore** to prevent future violations

**For developers with existing forks/clones:**
```bash
git pull origin main  # Get the cleanup commits
# Or for a fresh start:
git clone [repo-url]  # Re-clone to get clean history
```

**New .gitignore protections added:**
- `venv/` (virtual environments)
- `.cache/` (cache directories)  
- `.temp/` (temporary directories)
- Enhanced coverage for Python build artifacts

---

## Development Priorities

### High Priority
- [ ] **Performance optimization** - Profile voice loading and synthesis performance
- [ ] **Error handling** - Improve provider fallback mechanisms
- [ ] **Documentation** - Complete API reference documentation

### Medium Priority  
- [ ] **Testing coverage** - Expand provider-specific test coverage
- [ ] **Voice browser UX** - Enhance interface responsiveness
- [ ] **Configuration validation** - Add config file validation

### Low Priority
- [ ] **Provider expansion** - Investigate additional TTS providers
- [ ] **CLI enhancements** - Add more interactive features
- [ ] **Performance monitoring** - Add built-in performance metrics

---

## Notes

This TODO tracks both completed cleanup work and ongoing development priorities. The git cleanup was a one-time maintenance task to improve repository hygiene.