# Changelog

## What's Changed  in [v0.1.8]

- Refactor github CI workflows- ([a7c4655])

[v0.1.8]: https://github.com/glenn20/mpremote-path/compare/v0.1.7..v0.1.8
[a7c4655]: https://github.com/glenn20/mpremote-path/commit/a7c46551c3c04f361b2470bcd0c939e3ce30988a

## What's Changed  in [v0.1.7]

- Revert e51d3b9: Do not print the prompt after exiting raw REPL.- ([63b3db6])

[v0.1.7]: https://github.com/glenn20/mpremote-path/compare/v0.1.6..v0.1.7
[63b3db6]: https://github.com/glenn20/mpremote-path/commit/63b3db6d272fbf1ae92bef71681bf206e1233822

## What's Changed  in [v0.1.6]

- README.md: Fixup for CI badges.- ([4d3b9e9])
- pyproject.toml: Add python version metadata.- ([314d7b3])
- board.py: Deprecate `make_board()` function.- ([5de0d40])
- tests: Increase default baud rate from 115200 to 921600.- ([6406c9e])
- Update requirements.txt and uv.lock for security vuln in h11 package.- ([804edb0])
- Simplify pre-commit hooks and add post-checkout and post-commit hooks.- ([c7dc1bf])
- board.py: Print version number when debug logging is enabled.- ([cb7bafe])
- conftest.py: Trivial refactoring.- ([75c5eec])
- Update github workwlows to use the new ci-tox workflow.- ([07aa4a4])
- Empty commit to test CI.- ([33ab1b6])
- Use @dev for CI tests workflow.- ([0e2f974])
- github actions diagnostics- ([05272d0])
- Use @dev for python-ci workflows (for real this time).- ([55ac121])
- Diagnostics- ([0d1f3b6])
- pyproject.toml: Pass GITHUB_ACTIONS to tox environments.- ([82d4cf5])
- conftest.py: Minor refactor to cleanup running the micropython unix port.- ([0f73d3e])
- pyproject.toml: Fix usage of dependency_groups in tox config.- ([fb14f1e])
- pyproject.toml: Minor refactor of tox config for clarity.- ([01c297a])
- board.py: Add more detailed logging for method calls.- ([a334350])
- tests: Add support for running unix port tests without socat.- ([3df1598])
- board.py: Fix raw_repl handling for KeyboardInterrupt.- ([021f303])
- tests/unix_port.py: Major refactor of PTY bridge handling.- ([acca45e])
- WIP: Overhaul unix port tests and improve MPRemotePath.- ([bb2ca0e])
- test_base.py: Add test for MPath.mkdir() with parents=True.- ([b3daf3b])
- Fix: Update default baud rate in conftest.py.- ([9084ee1])
- board.py: Reprint the prompt when exiting the raw repl.- ([e51d3b9])
- mpremote_path: Fix stat check for empty entries.- ([eba4768])
- mpremote_path: Set home directory to initial dir on connect().- ([0bd787d])
- tests: Update tests to use the home directory set by connect().- ([5f6d4cf])
- pyproject.toml: Add support for github workflows with tox-gh.- ([30e09ab])

[v0.1.6]: https://github.com/glenn20/mpremote-path/compare/v0.1.5..v0.1.6
[4d3b9e9]: https://github.com/glenn20/mpremote-path/commit/4d3b9e9ef369ea5c11376b1a9d45af41cbb73d78
[314d7b3]: https://github.com/glenn20/mpremote-path/commit/314d7b306c8575b4ba3679e5aec5bb20d011a9a5
[5de0d40]: https://github.com/glenn20/mpremote-path/commit/5de0d40690329e13446b3893309e8be24bfdf494
[6406c9e]: https://github.com/glenn20/mpremote-path/commit/6406c9e60d5f11554cd6f463e47ddd8db170d954
[804edb0]: https://github.com/glenn20/mpremote-path/commit/804edb04dcf375b46099e0627d33784211f87a7a
[c7dc1bf]: https://github.com/glenn20/mpremote-path/commit/c7dc1bf3a5fe82b5e88aec45a2486db28f66d7e2
[cb7bafe]: https://github.com/glenn20/mpremote-path/commit/cb7bafe627df981d0faada006c41c4bbd09412be
[75c5eec]: https://github.com/glenn20/mpremote-path/commit/75c5eecc9542662dd1afb94f8b7f86d168e1fc43
[07aa4a4]: https://github.com/glenn20/mpremote-path/commit/07aa4a437d2b3916dad13d9025aeb3e6a4fcbc9c
[33ab1b6]: https://github.com/glenn20/mpremote-path/commit/33ab1b6cc348cc571f4c043db2824aee606491cc
[0e2f974]: https://github.com/glenn20/mpremote-path/commit/0e2f974d5688dc3e166443652585cb2615cb43cd
[05272d0]: https://github.com/glenn20/mpremote-path/commit/05272d0459d093fb3ef24c79530ece7e0983c291
[55ac121]: https://github.com/glenn20/mpremote-path/commit/55ac1214f328664503e95398a157f219514577f8
[0d1f3b6]: https://github.com/glenn20/mpremote-path/commit/0d1f3b6414c2bf8e259f04ec8e5f73709f2879e9
[82d4cf5]: https://github.com/glenn20/mpremote-path/commit/82d4cf53f7201db327bd0c55faddb8f13cf48a0e
[0f73d3e]: https://github.com/glenn20/mpremote-path/commit/0f73d3e41f53b10d0d108a67da2cf6b5c8bef4c9
[fb14f1e]: https://github.com/glenn20/mpremote-path/commit/fb14f1ea619cf9c796aadb9e425ff45a66ca7fbb
[01c297a]: https://github.com/glenn20/mpremote-path/commit/01c297a90099321ec8fef50025e032addf42f78b
[a334350]: https://github.com/glenn20/mpremote-path/commit/a334350de301de3f5058819440f2999e457457a0
[3df1598]: https://github.com/glenn20/mpremote-path/commit/3df159857dd57daebac899ef6f33a7e8ab8b12b8
[021f303]: https://github.com/glenn20/mpremote-path/commit/021f303fb7cdbd404fd50122c271869610bc0587
[acca45e]: https://github.com/glenn20/mpremote-path/commit/acca45e7dcd45b0c3f235cbbf7ca3e22dc351db0
[bb2ca0e]: https://github.com/glenn20/mpremote-path/commit/bb2ca0e4b6a3b40cc794278b1e9034c031f27b8b
[b3daf3b]: https://github.com/glenn20/mpremote-path/commit/b3daf3b7cfc5b7bbd3fb384ac1d6d6e02f9dea74
[9084ee1]: https://github.com/glenn20/mpremote-path/commit/9084ee11849be3f6c4e2627da9b3a31d0c578af7
[e51d3b9]: https://github.com/glenn20/mpremote-path/commit/e51d3b997c8a9da44da6fc2fc59df42a45be3b1c
[eba4768]: https://github.com/glenn20/mpremote-path/commit/eba47685613cbf742bc40c017ca60933141840e9
[0bd787d]: https://github.com/glenn20/mpremote-path/commit/0bd787d63dc2def0ae12a876c3c3c7cf0b6f3507
[5f6d4cf]: https://github.com/glenn20/mpremote-path/commit/5f6d4cf87dd1cf016e77e005d817f4ac1cbd1944
[30e09ab]: https://github.com/glenn20/mpremote-path/commit/30e09ab6c301660bfe5ebaf590a42de09025e006

## What's Changed  in [v0.1.5]

- board.py: Minor refactor of `Board.check_clock()` method.- ([51a22d7])
- tests: Add a unix micropython port for testing.- ([2ad1082])
- pyproject.toml: Add dependency_groups.- ([4c95b57])
- tests: Fix socat install for macos on github actions.- ([8681cd4])
- CI: Update CI workflows.- ([4d57cf6])
- CI: Skip Macos and Windows in CI tests.- ([d24c255])

[v0.1.5]: https://github.com/glenn20/mpremote-path/compare/v0.1.4..v0.1.5
[51a22d7]: https://github.com/glenn20/mpremote-path/commit/51a22d7e20e79ea48fe4dc293fb485e96f1048e5
[2ad1082]: https://github.com/glenn20/mpremote-path/commit/2ad1082ba0b08b95ade10152842c6f68bd228b6b
[4c95b57]: https://github.com/glenn20/mpremote-path/commit/4c95b57a53077e4e42dc6b3d639dc02fcb38736f
[8681cd4]: https://github.com/glenn20/mpremote-path/commit/8681cd4fc801a9732ac04b1b23b38c6eceefbf11
[4d57cf6]: https://github.com/glenn20/mpremote-path/commit/4d57cf66fc6c8deeee8e440b0861a67370a06a5c
[d24c255]: https://github.com/glenn20/mpremote-path/commit/d24c2552055a423173b9566df8d24b5ccc73c0a0

## What's Changed  in [v0.1.4]

- Add pre-commit config.- ([6e6a9f1])
- Add more detailed project metadata to pyproject.toml.- ([afb6103])
- tests: Skip all tests when run in github workflows- ([0433ea3])
- Add py.typed file to indicate the module is typed.- ([95a676d])
- github workflows. Revert to standard python-ci workflows.- ([62c3f2c])
- README.md: Add github and pypi badges.- ([0c17f23])
- conftest.py: Ignore exit status 5 (no tests collected)- ([7d87c3f])

[v0.1.4]: https://github.com/glenn20/mpremote-path/compare/v0.1.3..v0.1.4
[6e6a9f1]: https://github.com/glenn20/mpremote-path/commit/6e6a9f141910f01e7bc027f25d5969ff9bef5c5a
[afb6103]: https://github.com/glenn20/mpremote-path/commit/afb6103281c1dd6841eceab0523e0f5bac83c1bd
[0433ea3]: https://github.com/glenn20/mpremote-path/commit/0433ea3ec81807d3b113a0f8c2fcd94a9c482461
[95a676d]: https://github.com/glenn20/mpremote-path/commit/95a676de4b506529eb3dc7325f7f76ff0fafe4e1
[62c3f2c]: https://github.com/glenn20/mpremote-path/commit/62c3f2c476b23647e82e1527615267e328762ce2
[0c17f23]: https://github.com/glenn20/mpremote-path/commit/0c17f237b7e41c119d782c3f503967fd056ba055
[7d87c3f]: https://github.com/glenn20/mpremote-path/commit/7d87c3f11ca3fd1d1d9f1d854e092d4bf73ea669

## What's Changed  in [v0.1.3]

- Update README.md.- ([2a1a62a])
- Add github workflows for code checks, build, publish and release.- ([3249337])

[v0.1.3]: https://github.com/glenn20/mpremote-path/compare/v0.1.2..v0.1.3
[2a1a62a]: https://github.com/glenn20/mpremote-path/commit/2a1a62adb77feee2a44ae3ff88eb870cf0c9f1f9
[3249337]: https://github.com/glenn20/mpremote-path/commit/3249337adc40d4aa1c69d00ea9af8690f5f36a4e

## What's Changed  in [v0.1.2]

- tests: Fix newline conversion on Windows.- ([2045aff])
- tests: Add test/_data/src to repository.- ([fe5ae2a])
- Update requirements.txt from `uv pip compile` command.- ([748f1e4])
- pyproject.toml: Add support for posargs in pytest command.- ([5bb2d17])
- Handle Scandir paths correctly on Windows for python 3.13.- ([4d3efde])
- pyproject.toml: Move the [tool.tox] section to the end of the file.- ([c1428e4])
- pyproject.toml: mypy dont complain about unused ignores.- ([168ea35])

[v0.1.2]: https://github.com/glenn20/mpremote-path/compare/v0.1.1..v0.1.2
[2045aff]: https://github.com/glenn20/mpremote-path/commit/2045affd240165cafb7e72257107bfffd12b1ec6
[fe5ae2a]: https://github.com/glenn20/mpremote-path/commit/fe5ae2a35a674812a4470f005fbe7acd689a927d
[748f1e4]: https://github.com/glenn20/mpremote-path/commit/748f1e4534c6dc1af583ef871d0c8f688eac30a6
[5bb2d17]: https://github.com/glenn20/mpremote-path/commit/5bb2d17fd4a93c17551159389f650439376cc568
[4d3efde]: https://github.com/glenn20/mpremote-path/commit/4d3efde1ffbace7db949ddb22a22fe1ac7df38d3
[c1428e4]: https://github.com/glenn20/mpremote-path/commit/c1428e496b619173f3e01b4a9989dc06cdaa751f
[168ea35]: https://github.com/glenn20/mpremote-path/commit/168ea35137df96e545ef641e289d933ab42c12b3

## What's Changed  in [v0.1.1]

- pyproject.toml: Exclude mpremote v1.24.0 due to bug.- ([3eb7b4f])

[v0.1.1]: https://github.com/glenn20/mpremote-path/compare/v0.1.0..v0.1.1
[3eb7b4f]: https://github.com/glenn20/mpremote-path/commit/3eb7b4f3899e017e21097853af6103918dd88df7

## What's Changed  in [v0.1.0]

- borad.py: Minor refactor to use itertools.chain().- ([73af401])
- Remove use of START_CODE in mpremote_path.py.- ([f5db9d0])
- Add support for the MPRemotePath.open() method.- ([0a9d5de])
- pyproject.toml: Update to use `uv` for development environment.- ([69126a7])
- Add `typings` folder with type hints for mpremote `SerialTransport` class.- ([d3dcaaa])
- board.py: Update for strict typing compliance.- ([a6551f8])
- tests: Minor updates for python 3.13 and formatting.- ([d888ed4])
- mpremote_path.py: Extensive changes for python 3.13 and strict typing.- ([41d6591])
- mpfs.py and mpfsops.py: Update for strict typing compliance.- ([d6bc014])
- mpremote_path.py: Add open() overloads for BinaryIO.- ([c557a7e])

[v0.1.0]: https://github.com/glenn20/mpremote-path/compare/v0.0.1..v0.1.0
[73af401]: https://github.com/glenn20/mpremote-path/commit/73af4019b79154e8cf7ad82f14416eed432c760b
[f5db9d0]: https://github.com/glenn20/mpremote-path/commit/f5db9d08b2d76edfd1109ea969fce95c0666bf76
[0a9d5de]: https://github.com/glenn20/mpremote-path/commit/0a9d5de9bf4badf9f58b265a10cdf5a95db2e6ad
[69126a7]: https://github.com/glenn20/mpremote-path/commit/69126a74341c4f2b8691df63bf6706b2f10b8fc4
[d3dcaaa]: https://github.com/glenn20/mpremote-path/commit/d3dcaaa2565200ad4e3589da6bb662c9fc52bcbc
[a6551f8]: https://github.com/glenn20/mpremote-path/commit/a6551f8135d5c65fc076b29a9f14e376ebf9f093
[d888ed4]: https://github.com/glenn20/mpremote-path/commit/d888ed4b6d177676c3b94979dd1697715acb50e2
[41d6591]: https://github.com/glenn20/mpremote-path/commit/41d6591fbb2a1f9e83da1bfe81fed57755183986
[d6bc014]: https://github.com/glenn20/mpremote-path/commit/d6bc01427ab196f674cef5f2759de6472de98fa3
[c557a7e]: https://github.com/glenn20/mpremote-path/commit/c557a7e9b0835ab32369a8dfe9e840b9d56a5538

## What's Changed  in [v0.0.1]

- Initial commit- ([c7df0b9])
- First working implementation of RemotePath class.- ([c79e44b])
- Board.py: Mediate access to the mpremote SerialTransport instance.- ([1ecbbc7])
- Restructure the project to be a package.- ([1118768])
- board.py: Add Board.soft_reset() method.- ([c6be34a])
- RemotePath methods should return RemotePath, not Path types.- ([33f2546])
- Add tests and pyproject.toml.- ([b2c9683])
- Update to the scratch.py script providing examples of usage.- ([ec65b95])
- Rename RemotePath to MPRemotePath.- ([8d6fa9e])
- Update README.md with api docs.- ([17e0566])
- Remove scratch.py.- ([585cb78])
- Remove override for __repr__() in MPRemotePath.- ([3bb13c8])
- Implement MPRemotePath.replace() by calling MPRemotePath.rename().- ([00a8744])
- Add scratch.py to .gitignore.- ([0329ef7])
- Add `MPRemotePath.copy()` method.- ([5a4cd18])
- Implement samefile() for MPRemotePath.- ([68d3658])
- Add copyfile() method to MPRemotePath.- ([5700aa9])
- Use `str(p)` instead of `p.as_posix()` in mpremote_path.py.- ([fa6b75e])
- Protect `is_dir()` and `is_file()` from `FileNotFoundError`.- ([5a383d5])
- Board: add `exec_eval()` method.- ([d0d2be5])
- Board: Add `fs_stat()` method.- ([d55b7c0])
- Board: Add `check_time()` method to check the board's time and sync it- ([753214d])
- Use the new `fs_stat()` method in the Board class.- ([c0a7f98])
- Be more consistent in quoting path names in MPRemotePath.- ([33d75aa])
- Tests: Add options to synchronise board clock with host and use UTC.- ([f3a7c33])
- Bugfix: `exec_eval()` was not capturing the output of `exec()`.- ([9dc7b6b])
- Call `check_time()` from `make_board()` which takes the- ([aa0e5fe])
- A few tweaks...- ([06d981f])
- Add `logging` support to `mpremote_path.Board`.- ([aa83a86])
- `MPRemotePath.iterdir()` now uses `_scandir()` to get the list of files.- ([78b1e0c])
- Optimise the calls to `iterdir()` and `_scandir()`.- ([88b8daa])
- MPRemotePath.samefile() checks other type matches.- ([aadbdb2])
- Bugfix: MPRemotePath.iterdir() now returns an empty tuple if the- ([35375b7])
- Update README.md.- ([f0b7133])
- Dont reset the board after connecting.- ([57385a0])
- Add `mpremotepath` to exported symbols.- ([31a763f])
- Minor refactor:- ([5a53bbd])
- Delete the lru cache for _scandir() method.- ([65e181e])
- Add util.mpfs and util.mpfscmd modules.- ([8964344])
- Add tests for the util.mpfs and util.mpfscmd modules.- ([f206118])
- `get()`, `put()`, `cp()`, and `mv()` now return the destination path.- ([dc2e6b8])
- Add `is_wildcard_pattern()` to `mpremote_path` module.- ([35fb0fd])
- Fix teardown of `localdata` fixture in `conftest.py`.- ([e52d981])
- Rename util modules: mpfs->mpfsops and mpfscmd->mpfs.- ([d536049])
- Update README.md.- ([cd4ab1c])
- Rename the util test files to match the renamed util modules.- ([ec50213])
- Add requirements.txt for `mpremote`. and update README.md.- ([5bcca4b])
- Fix missing type annotation.- ([9703cae])
- Add `mpfs` script to `pyproject.toml` file.- ([5db91ca])
- Ensure `iterdir()` and `_scandir()` work when using multiple boards.- ([275ef9b])
- `mpfs.copyfile()` should raise an exception if `src` is not a regular file.- ([154bf91])
- Remove MPath.__init__() - all initialisation is in __new__().- ([61c092e])

[v0.0.1]: https://github.com/glenn20/mpremote-path/tree/v0.0.1
[c7df0b9]: https://github.com/glenn20/mpremote-path/commit/c7df0b9759119df6848eece5d0e5b56976500970
[c79e44b]: https://github.com/glenn20/mpremote-path/commit/c79e44b965ab8a41ac8a9c4179ce85cc9d94d1b6
[1ecbbc7]: https://github.com/glenn20/mpremote-path/commit/1ecbbc7bf1f907c140f13beeba8af12b943c5e02
[1118768]: https://github.com/glenn20/mpremote-path/commit/1118768144d1770ee9ca20db5ed5b289fcdfd838
[c6be34a]: https://github.com/glenn20/mpremote-path/commit/c6be34a1f30a29c43917f4c3d6edf4ba9599107b
[33f2546]: https://github.com/glenn20/mpremote-path/commit/33f254669cbb38abe4363eb3fe36095dd299be99
[b2c9683]: https://github.com/glenn20/mpremote-path/commit/b2c96833a15fc3cb8163276fabe45fb83f9986fc
[ec65b95]: https://github.com/glenn20/mpremote-path/commit/ec65b95a433eafc2d0f260363fa3779147e2d3b2
[8d6fa9e]: https://github.com/glenn20/mpremote-path/commit/8d6fa9e65f87b96ee33d25d21e898ae52ee3cfc7
[17e0566]: https://github.com/glenn20/mpremote-path/commit/17e056655808b3bc5ac5e46e4705d78ad9b343a4
[585cb78]: https://github.com/glenn20/mpremote-path/commit/585cb78ea458aa50466dca2deb14a7ca1ead1cf1
[3bb13c8]: https://github.com/glenn20/mpremote-path/commit/3bb13c8c14af84284724e43911cc033f6f9f2f7a
[00a8744]: https://github.com/glenn20/mpremote-path/commit/00a874415b6ea94d610fefb9abc3d43524657f44
[0329ef7]: https://github.com/glenn20/mpremote-path/commit/0329ef7f504696fafddb76f3c426f2e9e1458752
[5a4cd18]: https://github.com/glenn20/mpremote-path/commit/5a4cd18577e637878af9200096b64e83e050e19e
[68d3658]: https://github.com/glenn20/mpremote-path/commit/68d3658995ebc1ed6264e6b110a2d05506932f70
[5700aa9]: https://github.com/glenn20/mpremote-path/commit/5700aa994e7f3677fbd5c224cc74d378e16d36c2
[fa6b75e]: https://github.com/glenn20/mpremote-path/commit/fa6b75eaabf09c4c7fbefb13401d16e9193cf9e4
[5a383d5]: https://github.com/glenn20/mpremote-path/commit/5a383d5c9b8f43ab4b1f323b1a8ca06e93981ae5
[d0d2be5]: https://github.com/glenn20/mpremote-path/commit/d0d2be5dcb14d212036bdaf4b5c870846b74d3da
[d55b7c0]: https://github.com/glenn20/mpremote-path/commit/d55b7c0e1cc118288e144ef0d6bc84793bd491e5
[753214d]: https://github.com/glenn20/mpremote-path/commit/753214d81e3bf8eeeddbe064ea32d5c885ef72b7
[c0a7f98]: https://github.com/glenn20/mpremote-path/commit/c0a7f981b8125e40dd5a16c6fb84453216e9d1e8
[33d75aa]: https://github.com/glenn20/mpremote-path/commit/33d75aaaa3a21c731ccde30132ff4762b0dd569f
[f3a7c33]: https://github.com/glenn20/mpremote-path/commit/f3a7c33d6766734d090748e25d5578589d50a0e7
[9dc7b6b]: https://github.com/glenn20/mpremote-path/commit/9dc7b6b4626d583d9d7d3f73a2f553c997055e5b
[aa0e5fe]: https://github.com/glenn20/mpremote-path/commit/aa0e5fecce4e96efec1ffe418e1dbb002f37f025
[06d981f]: https://github.com/glenn20/mpremote-path/commit/06d981f623b4b021dd116cdf0a5873443540fbe8
[aa83a86]: https://github.com/glenn20/mpremote-path/commit/aa83a86b5b2408891c6ee84a3fff0cbfbf7ea223
[78b1e0c]: https://github.com/glenn20/mpremote-path/commit/78b1e0c89ddac21fa6c44d60b9c34d495176f0e9
[88b8daa]: https://github.com/glenn20/mpremote-path/commit/88b8daa05f569edf40614ca1859d184a12ff0fa2
[aadbdb2]: https://github.com/glenn20/mpremote-path/commit/aadbdb2293e6f7f01ff74c10cbb7ef3574bac9fd
[35375b7]: https://github.com/glenn20/mpremote-path/commit/35375b7be0da543697fe84f1095f77df57a4972f
[f0b7133]: https://github.com/glenn20/mpremote-path/commit/f0b713318205c1cb62214418bef0d90be736c8d5
[57385a0]: https://github.com/glenn20/mpremote-path/commit/57385a0d2e35f13c47e7220499834cac270aab85
[31a763f]: https://github.com/glenn20/mpremote-path/commit/31a763f3cde50a57bdd9f8158ccaa5e73f1ce412
[5a53bbd]: https://github.com/glenn20/mpremote-path/commit/5a53bbd259fe072824d7058c90d01c254b523fc4
[65e181e]: https://github.com/glenn20/mpremote-path/commit/65e181ee36e2928ed3350cb0bf301b76a8500788
[8964344]: https://github.com/glenn20/mpremote-path/commit/89643441188653abad461c55bf59e73f21e2ac68
[f206118]: https://github.com/glenn20/mpremote-path/commit/f206118914e98fb3e375e7aff32bf5c6b998851f
[dc2e6b8]: https://github.com/glenn20/mpremote-path/commit/dc2e6b8200a2964a3d5fb550f6ca84750bac8c06
[35fb0fd]: https://github.com/glenn20/mpremote-path/commit/35fb0fd3e8bf5ee9ea8f9d42fee8b625120b44f4
[e52d981]: https://github.com/glenn20/mpremote-path/commit/e52d981926e11b7d941f350486d93a32c7a87105
[d536049]: https://github.com/glenn20/mpremote-path/commit/d5360490430441240dc2de039ce326a49087707a
[cd4ab1c]: https://github.com/glenn20/mpremote-path/commit/cd4ab1c1c1fba0d1f90417573bee73e70683314d
[ec50213]: https://github.com/glenn20/mpremote-path/commit/ec502134915b98d14c9ebb3a37a1f4e0fc6fec20
[5bcca4b]: https://github.com/glenn20/mpremote-path/commit/5bcca4b551c2e99f07ea14f807e752f41dc63782
[9703cae]: https://github.com/glenn20/mpremote-path/commit/9703cae579e1b35b67b665547c2bf184abd16782
[5db91ca]: https://github.com/glenn20/mpremote-path/commit/5db91ca24e14b35eb9097bee3425dd862f04d0c6
[275ef9b]: https://github.com/glenn20/mpremote-path/commit/275ef9b8d257d7260452a0d1a6131e33803631af
[154bf91]: https://github.com/glenn20/mpremote-path/commit/154bf911facb41610b8b877aaf7ac794b056a3de
[61c092e]: https://github.com/glenn20/mpremote-path/commit/61c092e916e0bab5d90fa26a2e3d197746ce1fd6

<!-- generated by git-cliff -->
