"""Tests for scripts/importance_scoring.py"""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from importance_scoring import calculate_file_importance, normalize_path_scores


# =====================================================================
# 8. calculate_file_importance
# =====================================================================


class TestCalculateFileImportance:
    def test_src_main_ts_high_score(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        f = src / "main.ts"
        content = "x" * 2000  # 2000 bytes: 1KB <= size <= 50KB -> size_score = 1.0
        f.write_text(content, encoding="utf-8")
        score = calculate_file_importance(f, tmp_path, 2000)
        # path_score=1.0 (src), identity_score=1.0 (main), lang_score=1.0 (.ts), size_score=1.0
        assert score >= 0.8

    def test_config_lower_score(self, tmp_path):
        cfg = tmp_path / "config"
        cfg.mkdir()
        f = cfg / "settings.yaml"
        f.write_text("key: value\n", encoding="utf-8")
        score = calculate_file_importance(f, tmp_path, 10)
        # path_score=0.2 (config dir, not in IGNORE_DIRS), identity_score=0.3 (config in path),
        # lang_score=0.4 (.yaml), size_score=0.0 (<100)
        # 0.2*0.30 + 0.3*0.25 + 0.4*0.30 + 0.0*0.15 = 0.06+0.075+0.12 = 0.255
        assert score < 0.5

    def test_root_readme_moderate(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Hello\n" * 100, encoding="utf-8")  # 500 bytes approx
        size = len(("# Hello\n" * 100).encode("utf-8"))
        score = calculate_file_importance(f, tmp_path, size)
        # path_score=0.3 (root), identity_score=0.0 (README not a keyword), lang_score=0.0 (.md)
        # size depends on actual byte count; if 100B<=size<1KB -> size_score=0.5
        assert 0.0 <= score <= 1.0

    def test_all_scores_in_range(self, tmp_path):
        # Test a variety of files to ensure scores always fall in [0.0, 1.0]
        src = tmp_path / "src"
        src.mkdir()
        test_files = [
            src / "index.ts",       # high score
            tmp_path / "style.css", # low score
            tmp_path / "data.json", # moderate-low
        ]
        for tf in test_files:
            tf.write_text("x" * 500, encoding="utf-8")
            score = calculate_file_importance(tf, tmp_path, 500)
            assert 0.0 <= score <= 1.0


# =====================================================================
# 17. normalize_path_scores
# =====================================================================


class TestNormalizePathScores:
    """验证模块内 path_score 百分位归一化行为"""

    def _make_file(self, path, raw_path_score, identity=0.0, lang=1.0, size=1.0):
        score = raw_path_score * 0.30 + identity * 0.25 + lang * 0.30 + size * 0.15
        return {
            'path': path,
            'raw_path_score': raw_path_score,
            'raw_identity_score': identity,
            'raw_lang_score': lang,
            'raw_size_score': size,
            'importance_score': round(min(score, 1.0), 2),
            'is_core': score >= 0.5,
            'is_high_priority': score >= 0.6,
        }

    def test_single_file_module_sets_normalized_field(self):
        """单文件模块跳过百分位计算，但 path_score_normalized 字段必须存在"""
        files = [self._make_file('src/auth/service.py', raw_path_score=1.0)]
        modules = [{'path': 'src/auth', 'name': 'auth'}]
        result = normalize_path_scores(files, modules)
        assert 'path_score_normalized' in result[0], \
            "单文件模块也必须设置 path_score_normalized 字段"

    def test_single_file_module_recalculates_importance(self):
        """单文件模块跳过百分位，但 importance_score / is_core / is_high_priority 必须重算

        验证方式：构造一个文件，其原始 importance_score 与用 path_score_normalized 重算后不同，
        断言重算后的值（而非原始值）被写回。
        """
        # 原始 importance = 0.3*1.0 + 0.25*0.0 + 0.3*1.0 + 0.15*0.0 = 0.60
        # 归一化后 path_score_normalized = raw_path_score = 1.0（单文件模块保持原值）
        # 重算后 importance = 0.3*1.0 + 0.25*0.0 + 0.3*1.0 + 0.15*0.0 = 0.60（本例相同，无法区分）
        # 改用 identity=0.8, size=1.0：原始 = 0.3*1.0 + 0.25*0.8 + 0.3*1.0 + 0.15*1.0 = 0.95
        # 这里我们通过人为修改 importance_score 来验证重算确实发生
        f0 = self._make_file('src/auth/service.py', raw_path_score=1.0,
                             identity=0.8, lang=1.0, size=1.0)
        original_score = f0['importance_score']  # 0.95
        # 手动破坏 importance_score，模拟未重算情况
        f0['importance_score'] = 0.0
        f0['is_core'] = False
        f0['is_high_priority'] = False

        modules = [{'path': 'src/auth', 'name': 'auth'}]
        result = normalize_path_scores([f0], modules)
        f = result[0]
        # 重算后 importance_score 应该被修正（不再是我们手动设的 0.0）
        assert f['importance_score'] > 0.0, \
            "normalize_path_scores 必须对单文件模块重算 importance_score，不能保留破坏值 0.0"
        assert f['is_core'] == (f['importance_score'] >= 0.5)
        assert f['is_high_priority'] == (f['importance_score'] >= 0.6)

    def test_high_raw_score_gets_high_normalized(self):
        """同模块内原始分最高的文件，归一化后百分位最高"""
        files = [
            self._make_file('src/core/engine.py', raw_path_score=1.5),
            self._make_file('src/core/constants.py', raw_path_score=0.5),
            self._make_file('src/core/helpers.py', raw_path_score=0.3),
        ]
        modules = [{'path': 'src/core', 'name': 'core'}]
        result = normalize_path_scores(files, modules)
        by_path = {f['path']: f for f in result}
        assert by_path['src/core/engine.py']['path_score_normalized'] > \
               by_path['src/core/constants.py']['path_score_normalized'], \
               "高原始分文件应得到更高归一化分"

    def test_importance_score_valid_after_normalization(self):
        """归一化后所有文件的 importance_score 应在 0.0-1.0 之间"""
        files = [
            self._make_file('src/core/engine.py', raw_path_score=1.0),
            self._make_file('src/core/constants.py', raw_path_score=1.0),
        ]
        modules = [{'path': 'src/core', 'name': 'core'}]
        result = normalize_path_scores(files, modules)
        for f in result:
            assert 0.0 <= f['importance_score'] <= 1.0

    def test_cross_module_isolation(self):
        """不同模块的文件归一化互不影响"""
        files = [
            self._make_file('src/auth/service.py', raw_path_score=1.0),
            self._make_file('src/auth/model.py', raw_path_score=0.3),
            self._make_file('src/api/handler.py', raw_path_score=0.8),
            self._make_file('src/api/router.py', raw_path_score=0.2),
        ]
        modules = [
            {'path': 'src/auth', 'name': 'auth'},
            {'path': 'src/api', 'name': 'api'},
        ]
        result = normalize_path_scores(files, modules)
        by_path = {f['path']: f for f in result}
        assert by_path['src/auth/service.py']['path_score_normalized'] >= \
               by_path['src/auth/model.py']['path_score_normalized']
        assert by_path['src/api/handler.py']['path_score_normalized'] >= \
               by_path['src/api/router.py']['path_score_normalized']
