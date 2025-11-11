#!/usr/bin/env python3
"""
PatentPulse Reclaim Pack Generator (Phase IXe)
Generates PDF/JSON investor-ready reports of top patent opportunities

Usage:
  python jobs/reclaim_pack_generator.py --format pdf --limit 10
  FEATURE_PATENTPULSE_RECLAIM=true python jobs/reclaim_pack_generator.py --format pdf --limit 25 --country US
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

# PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not installed - PDF generation disabled")

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models.reclaim_pack import ReclaimPackExport, PatentExportItem, ReclaimPackData, ExportCriteria

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
patentpulse_items = db['patentpulse_items']
patentpulse_exports = db['patentpulse_exports']

# Config
EXPORT_DIR = os.environ.get('RECLAIM_EXPORT_DIR', '/app/exports')
EXPORT_TTL_DAYS = int(os.environ.get('EXPORT_TTL_DAYS', '7'))
MAX_EXPORT_ITEMS = int(os.environ.get('MAX_EXPORT_ITEMS', '100'))

# Legal disclaimer
FTO_DISCLAIMER = """
IMPORTANT LEGAL NOTICE:

PatentPulse data represents publicly available patent filings and derived analytics. 
This report is for INTERNAL INTELLIGENCE PURPOSES ONLY and does not constitute:
- Legal advice
- Freedom-to-Operate (FTO) clearance
- Guarantee of commercial viability

ALWAYS verify freedom-to-operate with qualified patent counsel before commercialization.
Patent statuses and rights may change. Conduct comprehensive due diligence.

Peptimancer™ disclaims all warranties. Use at your own risk.
"""


class ReclaimPackGenerator:
    """Generates reclaim pack exports (PDF/JSON)"""
    
    def __init__(self, criteria: ExportCriteria, output_format: str, output_dir: str):
        self.criteria = criteria
        self.format = output_format
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate(self) -> ReclaimPackExport:
        """Main generation workflow"""
        logger.info(f"Generating {self.format.upper()} reclaim pack with criteria: {self.criteria.model_dump()}")
        
        # 1. Load and score patents
        items = await self.load_patents()
        logger.info(f"Loaded {len(items)} candidate patents")
        
        # 2. Calculate viability scores
        scored_items = self.calculate_viability_scores(items)
        
        # 3. Sort and limit
        top_items = sorted(scored_items, key=lambda x: x['viability_score'], reverse=True)[:self.criteria.limit]
        logger.info(f"Selected top {len(top_items)} by viability score")
        
        # 4. Build export data
        export_items = [PatentExportItem(**item) for item in top_items]
        pack_data = self.build_pack_data(export_items)
        
        # 5. Generate file
        if self.format == 'json':
            file_path = await self.generate_json(pack_data)
        else:
            file_path = await self.generate_pdf(pack_data)
        
        # 6. Create export metadata
        file_stat = os.stat(file_path)
        export_meta = ReclaimPackExport(
            file_name=os.path.basename(file_path),
            format=self.format,
            criteria=self.criteria.model_dump(),
            count=len(export_items),
            expires_at=datetime.now(timezone.utc) + timedelta(days=EXPORT_TTL_DAYS),
            viability_avg=round(sum(item.viability_score for item in export_items) / len(export_items), 3) if export_items else 0.0,
            top_country=export_items[0].country if export_items else "N/A",
            file_path=str(file_path),
            size_kb=int(file_stat.st_size / 1024)
        )
        
        # 7. Save metadata to DB
        await patentpulse_exports.insert_one(export_meta.model_dump())
        
        logger.info(f"✅ Export complete: {file_path} ({export_meta.size_kb}KB)")
        
        return export_meta
    
    async def load_patents(self) -> List[Dict[str, Any]]:
        """Load patents from database with filters"""
        query = {}
        
        # Status filter
        if self.criteria.status_filter:
            query["status"] = {"$in": self.criteria.status_filter}
        else:
            # Default: Expired and ExpiringSoon
            query["status"] = {"$in": ["Expired", "ExpiringSoon"]}
        
        # Country filter
        if self.criteria.country_filter:
            query["country"] = self.criteria.country_filter
        
        # Min commercial score (baseline)
        query["commercial_score"] = {"$gte": 0.5}
        
        # Fetch
        cursor = patentpulse_items.find(query)
        items = await cursor.to_list(length=MAX_EXPORT_ITEMS)
        
        return items
    
    def calculate_viability_scores(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate viability score for each patent
        Formula: 0.6*commercial_score_adj + 0.2*(1-fto_risk) + 0.2*(1-synthesis_score)
        """
        scored = []
        
        for item in items:
            # Use adjusted score if available, else base score
            commercial = item.get('commercial_score_adj') or item.get('commercial_score', 0.5)
            fto_risk = item.get('fto_risk', 0.5)
            synthesis = item.get('synthesis_score', 0.5)
            
            viability = (
                0.6 * commercial +
                0.2 * (1 - fto_risk) +
                0.2 * (1 - synthesis)
            )
            
            item['viability_score'] = round(max(0.0, min(1.0, viability)), 3)
            scored.append(item)
        
        return scored
    
    def build_pack_data(self, items: List[PatentExportItem]) -> ReclaimPackData:
        """Build complete pack data structure"""
        # Count by status
        status_counts = {}
        country_counts = {}
        
        for item in items:
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
            country_counts[item.country] = country_counts.get(item.country, 0) + 1
        
        pack = ReclaimPackData(
            metadata={
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generator": "PatentPulse Reclaim Pack v1.0",
                "criteria": self.criteria.model_dump()
            },
            summary={
                "total_items": len(items),
                "avg_viability": round(sum(i.viability_score for i in items) / len(items), 3) if items else 0,
                "avg_commercial": round(sum(i.commercial_score_adj or i.commercial_score for i in items) / len(items), 3) if items else 0,
                "top_assignee": items[0].assignee if items else "N/A",
                "top_country": max(country_counts.items(), key=lambda x: x[1])[0] if country_counts else "N/A"
            },
            items=items,
            totals={
                "by_status": status_counts,
                "by_country": country_counts
            },
            disclaimer=FTO_DISCLAIMER
        )
        
        return pack
    
    async def generate_json(self, pack_data: ReclaimPackData) -> str:
        """Generate JSON export"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"patentpulse-reclaim-{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert to dict for JSON serialization
        data_dict = pack_data.model_dump()
        
        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        
        logger.info(f"JSON export saved: {filepath}")
        return str(filepath)
    
    async def generate_pdf(self, pack_data: ReclaimPackData) -> str:
        """Generate PDF export"""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab not installed - cannot generate PDF")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"patentpulse-reclaim-{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title page
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("PatentPulse™", title_style))
        story.append(Paragraph("Reclaim Pack Intelligence Report", styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary box
        summary_data = [
            ["Metric", "Value"],
            ["Total Opportunities", str(pack_data.summary['total_items'])],
            ["Avg Viability Score", f"{pack_data.summary['avg_viability']:.3f}"],
            ["Avg Commercial Score", f"{pack_data.summary['avg_commercial']:.3f}"],
            ["Top Assignee", pack_data.summary['top_assignee']],
            ["Top Country", pack_data.summary['top_country']]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        # Patent opportunities table
        story.append(Paragraph("Top Patent Opportunities", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Build table data
        table_data = [["Patent ID", "Title", "Assignee", "Country", "Status", "Viability"]]
        
        for item in pack_data.items[:20]:  # First 20 for PDF
            table_data.append([
                item.patent_id[:15],
                item.title[:40] + "..." if len(item.title) > 40 else item.title,
                item.assignee[:20],
                item.country,
                item.status[:10],
                f"{item.viability_score:.3f}"
            ])
        
        patent_table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1.3*inch, 0.6*inch, 0.9*inch, 0.7*inch])
        patent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(patent_table)
        story.append(PageBreak())
        
        # Disclaimer page
        story.append(Paragraph("Legal Disclaimer", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        disclaimer_paras = pack_data.disclaimer.strip().split('\n\n')
        for para in disclaimer_paras:
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF export saved: {filepath}")
        return str(filepath)


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="PatentPulse Reclaim Pack Generator")
    parser.add_argument("--format", choices=["pdf", "json"], default="pdf", help="Export format")
    parser.add_argument("--limit", type=int, default=10, help="Number of top patents")
    parser.add_argument("--country", type=str, help="Country filter (US, EP, JP, etc)")
    parser.add_argument("--status", type=str, help="Status filter (Expired, ExpiringSoon)")
    parser.add_argument("--out", type=str, default=EXPORT_DIR, help="Output directory")
    
    args = parser.parse_args()
    
    # Feature flag check
    if os.getenv("FEATURE_PATENTPULSE_RECLAIM", "false").lower() != "true":
        logger.error("❌ FEATURE_PATENTPULSE_RECLAIM=true required")
        sys.exit(1)
    
    # Build criteria
    criteria = ExportCriteria(
        limit=min(args.limit, MAX_EXPORT_ITEMS),
        status_filter=[args.status] if args.status else None,
        country_filter=args.country
    )
    
    # Generate
    generator = ReclaimPackGenerator(criteria, args.format, args.out)
    export_meta = await generator.generate()
    
    # Print result
    print("\n" + "="*60)
    print("✅ RECLAIM PACK GENERATED")
    print("="*60)
    print(f"File: {export_meta.file_name}")
    print(f"Format: {export_meta.format.upper()}")
    print(f"Items: {export_meta.count}")
    print(f"Size: {export_meta.size_kb}KB")
    print(f"Avg Viability: {export_meta.viability_avg:.3f}")
    print(f"Expires: {export_meta.expires_at.strftime('%Y-%m-%d')}")
    print(f"Path: {export_meta.file_path}")
    print("="*60 + "\n")
    
    client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
