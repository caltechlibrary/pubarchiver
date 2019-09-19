# =============================================================================
# @file    Makefile
# @brief   Makefile for some steps in creating Microarchiver releases
# @author  Michael Hucka
# @date    2019-09-19
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/microarchiver
# =============================================================================

release:;
	sed -i .bak -e "/version/ s/[0-9].[0-9].[0-9]/$$(<VERSION.txt)/" codemeta.json
	git add codemeta.json
	git commit -m"Update version number" codemeta.json
	git tag -a v$$(<VERSION.txt) -m "Release $$(<VERSION.txt)"
	git push -v --all
	git push -v --tags
