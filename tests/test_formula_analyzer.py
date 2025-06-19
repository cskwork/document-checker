"""
수식 분석기 테스트 모듈

이 모듈은 FormulaAnalyzer 클래스의 기능을 테스트합니다.
"""

import unittest
from src.content_analyzer.formula_analyzer import FormulaAnalyzer

class TestFormulaAnalyzer(unittest.TestCase):
    """FormulaAnalyzer 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.analyzer = FormulaAnalyzer()
        self.test_doc = {
            'id': 'test_doc_1',
            'content': {
                'text': 'This is a test document with formula E = mc^2 and another formula f(x) = x^2.'
            }
        }
    
    def test_enrich_document_with_formulas(self):
        """수식 인식 테스트"""
        enriched_doc = self.analyzer.enrich_document_with_formulas(self.test_doc)
        
        # 수식 정보가 추가되었는지 확인
        self.assertIn('enrichments', enriched_doc['content'])
        self.assertIn('formulas', enriched_doc['content']['enrichments'])
        
        # 수식이 올바르게 인식되었는지 확인
        formulas = enriched_doc['content']['enrichments']['formulas']
        self.assertGreaterEqual(len(formulas), 2)  # 최소 2개의 수식이 있어야 함
        
        # 첫 번째 수식 확인
        formula1 = next((f for f in formulas if 'E = mc^2' in f['text']), None)
        self.assertIsNotNone(formula1)
        self.assertEqual(formula1['type'], 'equation')
        
        # 두 번째 수식 확인
        formula2 = next((f for f in formulas if 'f(x) = x^2' in f['text']), None)
        self.assertIsNotNone(formula2)
        self.assertEqual(formula2['type'], 'equation')
    
    def test_search_formulas(self):
        """수식 검색 테스트"""
        # 먼저 문서에 수식 정보 추가
        enriched_doc = self.analyzer.enrich_document_with_formulas(self.test_doc)
        
        # 수식 검색
        matches = self.analyzer.search_formulas(enriched_doc, 'E=mc^2')
        
        # 검색 결과 확인
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0]['documentId'], 'test_doc_1')
        self.assertEqual(matches[0]['pattern'], 'E=mc^2')
    
    def test_formula_normalization(self):
        """수식 정규화 테스트"""
        # 다양한 형식의 수식 정규화
        formula1 = 'E = mc^2'
        formula2 = '$E = mc^2$'
        
        normalized1 = self.analyzer._normalize_formula(formula1)
        normalized2 = self.analyzer._normalize_formula(formula2)
        
        # 정규화 결과 확인
        self.assertEqual(normalized1, 'E=mc^2')
        self.assertEqual(normalized2, 'E=mc^2')
    
    def test_variable_extraction(self):
        """변수 추출 테스트"""
        formula = 'E = mc^2'
        variables = self.analyzer._extract_variables(formula)
        
        # 변수 추출 결과 확인
        self.assertIn('E', variables)
        self.assertIn('m', variables)
        self.assertIn('c', variables)
    
    def test_formula_type_determination(self):
        """수식 유형 결정 테스트"""
        equation = 'E = mc^2'
        expression = 'a + b - c'
        
        # 유형 결정 결과 확인
        self.assertEqual(self.analyzer._determine_formula_type(equation), 'equation')
        self.assertEqual(self.analyzer._determine_formula_type(expression), 'expression')

if __name__ == '__main__':
    unittest.main()
