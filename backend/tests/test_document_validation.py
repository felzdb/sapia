import unittest

from app.documents import (
    is_date_before,
    is_future_date,
    is_valid_benefit_number,
    is_valid_benefit_value,
    is_valid_competencia,
    is_valid_date,
    is_valid_name,
    is_valid_nit_pis,
)


class DocumentValidationTests(unittest.TestCase):
    def test_valid_name(self):
        self.assertTrue(is_valid_name("Maria da Silva"))
        self.assertTrue(is_valid_name("Canaan"))
        self.assertTrue(is_valid_name("Aaaabner"))
        self.assertTrue(is_valid_name("Ana-Maria"))

    def test_invalid_name(self):
        self.assertFalse(is_valid_name("aaaaaaaaaaaa"))
        self.assertFalse(is_valid_name("Maria123"))
        self.assertFalse(is_valid_name("João@Silva"))

    def test_valid_and_invalid_dates(self):
        self.assertTrue(is_valid_date("15/03/1965"))
        self.assertFalse(is_valid_date("31/02/2026"))
        self.assertFalse(is_valid_date("00/00/0000"))

    def test_future_birth_date(self):
        self.assertTrue(is_future_date("31/12/2999"))
        self.assertFalse(is_future_date("15/03/1965"))

    def test_date_before_reference(self):
        self.assertTrue(
            is_date_before("01/01/1960", "15/03/1965")
        )
        self.assertFalse(
            is_date_before("01/08/2026", "15/03/1965")
        )

    def test_competencia(self):
        self.assertTrue(is_valid_competencia("08/2026"))
        self.assertFalse(is_valid_competencia("13/2026"))
        self.assertFalse(is_valid_competencia("00/2026"))

    def test_benefit_value(self):
        self.assertTrue(is_valid_benefit_value("R$ 2.350,00"))
        self.assertFalse(is_valid_benefit_value("R$ 0,00"))
        self.assertFalse(is_valid_benefit_value("abc"))

    def test_nit_pis(self):
        self.assertTrue(is_valid_nit_pis("123.45678.90-0"))
        self.assertFalse(is_valid_nit_pis("123.45678.90-1"))
        self.assertFalse(is_valid_nit_pis("000.00000.00-0"))
        self.assertFalse(is_valid_nit_pis("ABC12345678901"))

    def test_benefit_number(self):
        self.assertTrue(is_valid_benefit_number("123.456.789-7"))
        self.assertFalse(is_valid_benefit_number("000.000.000-0"))
        self.assertFalse(is_valid_benefit_number("12345"))
        self.assertFalse(is_valid_benefit_number("ABC1234567890"))


if __name__ == "__main__":
    unittest.main()
    