# Ultra ERP - 300K Line Architecture

## Tech Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI (REST API)
- **DB**: SQLite (development) / PostgreSQL (production-ready schema)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Testing**: pytest + pytest-asyncio
- **Types**: Full type hints (mypy strict)
- **Package**: Each module = independent Python package under `src/`

## Directory Structure

```
erp-ultra/
├── src/
│   ├── foundation/          # Phase 0: 基盤 (15 modules)
│   │   ├── 001_database/
│   │   ├── 002_auth/
│   │   ├── 003_rbac/
│   │   ├── 004_api_gateway/
│   │   ├── 005_config/
│   │   ├── 006_logging/
│   │   ├── 007_queue/
│   │   ├── 008_cache/
│   │   ├── 009_migration/
│   │   ├── 010_event_bus/
│   │   ├── 011_validators/
│   │   ├── 012_serializers/
│   │   ├── 013_errors/
│   │   ├── 014_middleware/
│   │   └── 015_health/
│   ├── domain/              # Phase 1: 共通ドメイン (20 modules)
│   │   ├── 016_customer_model/
│   │   ├── 017_product_model/
│   │   ├── 018_supplier_model/
│   │   ├── 019_department/
│   │   ├── 020_fiscal_period/
│   │   ├── 021_tax_engine/
│   │   ├── 022_currency/
│   │   ├── 023_address/
│   │   ├── 024_contact/
│   │   ├── 025_document_number/
│   │   ├── 026_unit_of_measure/
│   │   ├── 027_warehouse_model/
│   │   ├── 028_pricing/
│   │   ├── 029_payment_terms/
│   │   ├── 030_attachment/
│   │   ├── 031_audit_log/
│   │   ├── 032_notification/
│   │   ├── 033_workflow/
│   │   ├── 034_approval/
│   │   └── 035_localization/
│   ├── sales/               # Phase 2: 販売管理 (15 modules)
│   │   ├── 036_quotation/
│   │   ├── 037_sales_order/
│   │   ├── 038_shipment/
│   │   ├── 039_invoice/
│   │   ├── 040_sales_return/
│   │   ├── 041_sales_analytics/
│   │   ├── 042_commission/
│   │   ├── 043_price_list/
│   │   ├── 044_discount/
│   │   ├── 045_sales_forecast/
│   │   ├── 046_customer_portal/
│   │   ├── 047_sales_team/
│   │   ├── 048_contract/
│   │   ├── 049_promotion/
│   │   └── 050_sales_report/
│   ├── inventory/           # Phase 3: 在庫管理 (15 modules)
│   │   ├── 051_stock_receipt/
│   │   ├── 052_stock_issue/
│   │   ├── 053_stock_transfer/
│   │   ├── 054_inventory_count/
│   │   ├── 055_lot_tracking/
│   │   ├── 056_serial_tracking/
│   │   ├── 057_warehouse_mgmt/
│   │   ├── 058_bin_location/
│   │   ├── 059_reorder_point/
│   │   ├── 060_stock_alert/
│   │   ├── 061_inventory_valuation/
│   │   ├── 062_stock_aging/
│   │   ├── 063_bom_inventory/
│   │   ├── 064_inventory_report/
│   │   └── 065_inventory_api/
│   ├── procurement/         # Phase 4: 購買管理 (15 modules)
│   │   ├── 066_purchase_request/
│   │   ├── 067_purchase_order/
│   │   ├── 068_goods_receipt/
│   │   ├── 069_supplier_eval/
│   │   ├── 070_purchase_return/
│   │   ├── 071_quotation_cmp/
│   │   ├── 072_blanket_order/
│   │   ├── 073_purchase_contract/
│   │   ├── 074_vendor_payment/
│   │   ├── 075_purchase_analytics/
│   │   ├── 076_lead_time/
│   │   ├── 077_purchase_approval/
│   │   ├── 078_cost_allocation/
│   │   ├── 079_purchase_schedule/
│   │   └── 080_procurement_report/
│   ├── finance/             # Phase 5: 財務会計 (20 modules)
│   │   ├── 081_journal_entry/
│   │   ├── 082_general_ledger/
│   │   ├── 083_trial_balance/
│   │   ├── 084_balance_sheet/
│   │   ├── 085_income_statement/
│   │   ├── 086_cash_flow/
│   │   ├── 087_accounts_receivable/
│   │   ├── 088_accounts_payable/
│   │   ├── 089_fixed_assets/
│   │   ├── 090_depreciation/
│   │   ├── 091_tax_return/
│   │   ├── 092_bank_reconcile/
│   │   ├── 093_closing/
│   │   ├── 094_cost_center/
│   │   ├── 095_segment_report/
│   │   ├── 096_intercompany/
│   │   ├── 097_retained_earnings/
│   │   ├── 098_dividend/
│   │   ├── 099_consolidation/
│   │   └── 100_finance_report/
│   ├── management/          # Phase 6: 管理会計 (15 modules)
│   │   ├── 101_budget/
│   │   ├── 102_cost_accounting/
│   │   ├── 103_profit_center/
│   │   ├── 104_variance/
│   │   ├── 105_break_even/
│   │   ├── 106_cash_budget/
│   │   ├── 107_transfer_pricing/
│   │   ├── 108_activity_cost/
│   │   ├── 109_standard_cost/
│   │   ├── 110_project_cost/
│   │   ├── 111_department_pnl/
│   │   ├── 112_forecasting/
│   │   ├── 113_kpi_dashboard/
│   │   ├── 114_management_report/
│   │   └── 115_decision_support/
│   ├── hr/                  # Phase 7: 人事・給与 (20 modules)
│   │   ├── 116_employee/
│   │   ├── 117_attendance/
│   │   ├── 118_leave/
│   │   ├── 119_overtime/
│   │   ├── 120_payroll/
│   │   ├── 121_bonus/
│   │   ├── 122_social_insurance/
│   │   ├── 123_income_tax/
│   │   ├── 124_year_end_adj/
│   │   ├── 125_expense/
│   │   ├── 126_recruitment/
│   │   ├── 127_evaluation/
│   │   ├── 128_training/
│   │   ├── 129_org_chart/
│   │   ├── 130_benefits/
│   │   ├── 131_labor_contract/
│   │   ├── 132_shift_schedule/
│   │   ├── 133_hr_report/
│   │   ├── 134_retirement/
│   │   └── 135_payslip/
│   ├── production/          # Phase 8: 生産管理 (15 modules)
│   │   ├── 136_bom/
│   │   ├── 137_routing/
│   │   ├── 138_work_order/
│   │   ├── 139_production_schedule/
│   │   ├── 140_quality_control/
│   │   ├── 141_quality_inspection/
│   │   ├── 142_mrp/
│   │   ├── 143_capacity_planning/
│   │   ├── 144_shop_floor/
│   │   ├── 145_scrap_tracking/
│   │   ├── 146_production_cost/
│   │   ├── 147_maintenance/
│   │   ├── 148_production_report/
│   │   └── 149_production_api/
│   ├── crm/                 # Phase 9: CRM (10 modules)
│   │   ├── 150_lead/
│   │   ├── 151_opportunity/
│   │   ├── 152_activity/
│   │   ├── 153_campaign/
│   │   ├── 154_email_marketing/
│   │   ├── 155_customer_segment/
│   │   ├── 156_satisfaction/
│   │   ├── 157_case_mgmt/
│   │   ├── 158_knowledge_base/
│   │   └── 159_crm_analytics/
│   ├── frontend/            # Phase 10: UI (25 modules)
│   │   ├── 160_dashboard_ui/
│   │   ├── 161_sales_ui/
│   │   ├── 162_inventory_ui/
│   │   ├── 163_procurement_ui/
│   │   ├── 164_finance_ui/
│   │   ├── 165_hr_ui/
│   │   ├── 166_production_ui/
│   │   ├── 167_crm_ui/
│   │   ├── 168_report_builder/
│   │   ├── 169_form_builder/
│   │   ├── 170_data_table/
│   │   ├── 171_chart_widget/
│   │   ├── 172_file_upload/
│   │   ├── 173_search/
│   │   ├── 174_notification_ui/
│   │   ├── 175_approval_ui/
│   │   ├── 176_workflow_ui/
│   │   ├── 177_settings_ui/
│   │   ├── 178_login_ui/
│   │   ├── 179_menu_nav/
│   │   ├── 180_import_export/
│   │   ├── 181_print_template/
│   │   ├── 182_audit_trail_ui/
│   │   └── 183_help_system/
│   └── integration/         # Phase 11: 連携 (12 modules)
│       ├── 184_bank_api/
│       ├── 185_edi/
│       ├── 186_pdf_gen/
│       ├── 187_email/
│       ├── 188_slack/
│       ├── 189_spreadsheet/
│       ├── 190_webhook/
│       ├── 191_sso/
│       ├── 192_backup/
│       ├── 193_data_import/
│       ├── 194_data_export/
│       └── 195_migration/
├── tests/
│   └── integration/         # Phase 12: 統合テスト
│       ├── 196_e2e_sales/
│       ├── 197_e2e_procure_to_pay/
│       ├── 198_e2e_production/
│       ├── 199_e2e_payroll/
│       └── 200_e2e_close/
├── shared/                  # 共通定義（Claudeが実装）
│   ├── schema.py            # DB schema constants
│   ├── types.py             # 共通型定義
│   ├── errors.py            # エラー基底クラス
│   └── interfaces.py        # モジュール間I/F
└── README.md
```

## Module Contract（各モジュールが守るべきルール）

### 1. ディレクトリ構造（統一）
```
src/{layer}/{NNN_name}/
├── __init__.py          # Public API export
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas (request/response)
├── service.py           # Business logic
├── router.py            # FastAPI routes
├── validators.py        # Input validation
├── tests/
│   ├── test_models.py
│   ├── test_service.py
│   ├── test_router.py
│   └── test_validators.py
└── README.md
```

### 2. インターフェース約束
- **models.py**: `from shared.types import BaseModel` を継承
- **schemas.py**: Pydantic BaseModelで入出力定義
- **service.py**: 純粋関数ベース、DB依存は引数で注入
- **router.py**: `/api/v1/{module-name}` プレフィックス

### 3. 依存ルール
- **shared/** のみに依存可能（他モジュールへの直接import禁止）
- モジュール間通信は Event Bus 経由または REST API
- 各モジュールは単体でテスト可能

### 4. 品質要件
- 型ヒント: 全public関数・メソッド
- Docstring: 全public関数・クラス
- テスト: モデル・サービス・ルーターの各レイヤー
- エラーハンドリング: shared.errors のカスタム例外を使用

## 共通型定義 (shared/types.py)

```python
# Base types all modules use
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel as PydanticBase
from enum import Enum

T = TypeVar('T')

class BaseSchema(PydanticBase):
    """All Pydantic schemas inherit from this"""
    class Config:
        from_attributes = True

class AuditableMixin(BaseSchema):
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

class SoftDeleteMixin(BaseSchema):
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

class PaginatedResponse(BaseSchema, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

class Money(BaseSchema):
    amount: Decimal
    currency: str = "JPY"

class Address(BaseSchema):
    postal_code: str
    prefecture: str
    city: str
    street: str
    building: Optional[str] = None

class ContactInfo(BaseSchema):
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    mobile: Optional[str] = None

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class TaxType(str, Enum):
    STANDARD_10 = "standard_10"
    REDUCED_8 = "reduced_8"
    EXEMPT = "exempt"
```

## DB Schema Constants (shared/schema.py)

```python
# Table name constants and column conventions
TABLE_PREFIX = ""
ID_COLUMN = "id"
CODE_COLUMN = "code"
NAME_COLUMN = "name"

# Common column definitions
class Columns:
    ID = ("id", "Integer, primary_key=True")
    CODE = ("code", "String(50), unique=True, nullable=False")
    NAME = ("name", "String(200), nullable=False")
    DESCRIPTION = ("description", "Text")
    STATUS = ("status", "String(20), default='draft'")
    AMOUNT = ("amount", "Numeric(15,2), default=0")
    QUANTITY = ("quantity", "Numeric(15,3), default=0")
    DATE = ("date", "Date")
    DATETIME = ("datetime", "DateTime")
    FK = lambda ref: (f"{ref}_id", f"Integer, ForeignKey('{ref}.id')")
    CREATED_AT = ("created_at", "DateTime, default=func.now()")
    UPDATED_AT = ("updated_at", "DateTime, default=func.now(), onupdate=func.now()")
```

## Event Bus Contract (shared/interfaces.py)

```python
from typing import Any, Callable
from dataclasses import dataclass

@dataclass
class Event:
    event_type: str
    module: str
    data: dict[str, Any]
    timestamp: datetime

class EventBus:
    """Module-to-module async communication"""
    async def publish(self, event: Event) -> None: ...
    async def subscribe(self, event_type: str, handler: Callable) -> None: ...
    async def unsubscribe(self, event_type: str, handler: Callable) -> None: ...
```

## Inter-module Dependencies Map

```
Phase 0: foundation (依存なし - 全モジュールが独立)
  ↓
Phase 1: domain (foundation にのみ依存)
  ↓
Phase 2-9: 各業務モジュール (foundation + domain のみ依存)
  ↓
Phase 10: frontend (全業務モジュールのスキーマに依存)
  ↓
Phase 11: integration (特定モジュールに依存)
  ↓
Phase 12: e2e tests (全モジュールに依存)
```

## Issue Template (for Jules)

Each issue will contain:
1. Module name and number
2. Functional requirements (detailed)
3. File structure to create
4. Models to implement (with field definitions)
5. API endpoints to implement
6. Business logic rules
7. Test requirements (unit + integration)
8. Dependencies (shared/ only)
9. Quality checklist
