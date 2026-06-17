#!/usr/bin/env python3
"""
Enhanced Dashboard Analytics Module - Most Advanced Version
Provides comprehensive, efficient business intelligence for the Invoice Management System
Optimized with SQL aggregates for maximum performance
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract
from collections import defaultdict
from calendar import monthrange
import math

# Import the models from app
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_dashboard_data(date_filter=None, db_session=None, models=None):
    """
    Generate comprehensive dashboard analytics data using optimized SQL queries
    Args:
        date_filter: Optional date range filter (start_date, end_date)
        db_session: Optional database session (if None, will import from app)
        models: Optional dict with models (if None, will import from app)
    Returns: Dictionary with all dashboard metrics
    """
    try:
        # Import models and db - use provided or import from app
        if models is not None and db_session is not None:
            # Use provided models and db session
            db = db_session
            Invoice = models.get('Invoice')
            Customer = models.get('Customer')
            Company = models.get('Company')
            PurchaseOrder = models.get('PurchaseOrder')
            Vendor = models.get('Vendor')
            InvoiceItem = models.get('InvoiceItem')
            PaymentRecord = models.get('PaymentRecord')
        else:
            # Import from app (fallback)
            from app import db as app_db, Invoice, Customer, Company, PurchaseOrder, Vendor, InvoiceItem, PaymentRecord
            db = db_session if db_session else app_db
        
        # Ensure we have all required models
        if not all([db, Invoice, Customer]):
            raise ImportError("Failed to import required database models")
        
        # Date ranges for analytics
        today = date.today()
        current_month_start = today.replace(day=1)
        previous_month = current_month_start - timedelta(days=1)
        previous_month_start = previous_month.replace(day=1)
        year_start = today.replace(month=1, day=1)
        week_start = today - timedelta(days=today.weekday())
        quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
        
        # Check if PostgreSQL or SQLite
        is_postgresql = 'postgresql' in str(db.engine.url)
        
        # OPTIMIZED: Use SQL aggregates instead of loading all records
        # 1. REVENUE METRICS - Single query with aggregates
        try:
            total_revenue_query = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('total_revenue'),
                func.count(Invoice.id).label('total_count')
            ).first()
            
            if total_revenue_query:
                total_revenue = float(total_revenue_query.total_revenue or 0)
                total_invoices = int(total_revenue_query.total_count or 0)
            else:
                total_revenue = 0.0
                total_invoices = 0
                
        except Exception as query_error:
            print(f"DEBUG: Revenue query failed: {query_error}")
            import traceback
            traceback.print_exc()
            total_revenue = 0.0
            total_invoices = 0
        
        # Current month revenue
        try:
            current_month_query = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('count')
            ).filter(
                and_(
                    Invoice.invoice_date >= current_month_start,
                    Invoice.invoice_date <= today
                )
            ).first()
            
            current_month_revenue = float(current_month_query.revenue or 0)
            current_month_count = current_month_query.count or 0
            
            # Current month collections
            current_month_paid_query = db.session.query(
                func.coalesce(func.sum(PaymentRecord.total_amount), 0).label('paid')
            ).filter(
                and_(
                    PaymentRecord.payment_date >= current_month_start,
                    PaymentRecord.payment_date <= today
                )
            ).first()
            current_month_paid = float(current_month_paid_query.paid or 0)
        except:
            current_month_revenue = 0.0
            current_month_count = 0
            current_month_paid = 0.0
        
        # Previous month revenue
        try:
            previous_month_query = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('count')
            ).filter(
                and_(
                    Invoice.invoice_date >= previous_month_start,
                    Invoice.invoice_date < current_month_start
                )
            ).first()
            
            previous_month_revenue = float(previous_month_query.revenue or 0)
            previous_month_count = previous_month_query.count or 0
        except:
            previous_month_revenue = 0.0
            previous_month_count = 0
        
        # Week revenue
        try:
            week_query = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('count')
            ).filter(
                Invoice.invoice_date >= week_start
            ).first()
            
            week_revenue = float(week_query.revenue or 0)
            week_count = week_query.count or 0
        except:
            week_revenue = 0.0
            week_count = 0
        
        # Revenue growth calculation
        revenue_growth = 0
        if previous_month_revenue > 0:
            revenue_growth = ((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100
        
        # Invoice growth
        invoice_growth = 0
        if previous_month_count > 0:
            invoice_growth = ((current_month_count - previous_month_count) / previous_month_count) * 100
        
        # 2. PAYMENT STATUS BREAKDOWN - Optimized single query
        try:
            payment_status_query = db.session.query(
                Invoice.status,
                func.coalesce(func.sum(Invoice.total_amount), 0).label('amount'),
                func.count(Invoice.id).label('count')
            ).group_by(Invoice.status).all()
            
            unpaid_amount = 0
            paid_amount = 0
            partially_paid_amount = 0
            unpaid_count = 0
            paid_count = 0
            partially_paid_count = 0
            
            for status, amount, count in payment_status_query:
                if status == 'unpaid':
                    unpaid_amount = float(amount)
                    unpaid_count = count
                elif status == 'paid':
                    paid_amount = float(amount)
                    paid_count = count
                elif status == 'partially_paid':
                    partially_paid_amount = float(amount)
                    partially_paid_count = count
        except:
            unpaid_amount = 0
            paid_amount = 0
            partially_paid_amount = 0
            unpaid_count = 0
            paid_count = 0
            partially_paid_count = 0
        
        outstanding_amount = unpaid_amount + partially_paid_amount
        
        # 3. GST BREAKDOWN - Optimized query
        try:
            gst_query = db.session.query(
                func.coalesce(func.sum(Invoice.cgst_amount), 0).label('cgst'),
                func.coalesce(func.sum(Invoice.sgst_amount), 0).label('sgst'),
                func.coalesce(func.sum(Invoice.igst_amount), 0).label('igst')
            ).first()
            
            total_cgst = float(gst_query.cgst or 0)
            total_sgst = float(gst_query.sgst or 0)
            total_igst = float(gst_query.igst or 0)
            total_gst = total_cgst + total_sgst + total_igst
        except:
            total_cgst = 0.0
            total_sgst = 0.0
            total_igst = 0.0
            total_gst = 0.0
        
        # Current month GST
        try:
            current_month_gst_query = db.session.query(
                func.coalesce(func.sum(Invoice.cgst_amount), 0).label('cgst'),
                func.coalesce(func.sum(Invoice.sgst_amount), 0).label('sgst'),
                func.coalesce(func.sum(Invoice.igst_amount), 0).label('igst')
            ).filter(
                and_(
                    Invoice.invoice_date >= current_month_start,
                    Invoice.invoice_date <= today
                )
            ).first()
            
            current_month_cgst = float(current_month_gst_query.cgst or 0)
            current_month_sgst = float(current_month_gst_query.sgst or 0)
            current_month_igst = float(current_month_gst_query.igst or 0)
            current_month_gst = current_month_cgst + current_month_sgst + current_month_igst
        except:
            current_month_cgst = 0.0
            current_month_sgst = 0.0
            current_month_igst = 0.0
            current_month_gst = 0.0
        
        # 4. TOP CUSTOMERS ANALYSIS - Optimized with JOIN
        try:
            top_customers_revenue_query = db.session.query(
                Customer.name,
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('invoice_count')
            ).join(Invoice).group_by(Customer.id, Customer.name).order_by(
                func.sum(Invoice.total_amount).desc()
            ).limit(10).all()
            
            top_customers_revenue = [(row.name, float(row.revenue), row.invoice_count) for row in top_customers_revenue_query]
            top_customers_count = sorted(top_customers_revenue, key=lambda x: x[2], reverse=True)[:10]
        except:
            top_customers_revenue = []
            top_customers_count = []
        
        # 5. MONTHLY TREND DATA (Last 12 months) - Fixed calculation
        monthly_data = []
        try:
            # Generate last 12 months
            for i in range(11, -1, -1):  # Last 12 months, newest first
                # Calculate month date correctly
                month_offset = i
                if month_offset == 0:
                    month_date = current_month_start
                else:
                    # Go back month_offset months
                    year = today.year
                    month = today.month
                    for _ in range(month_offset):
                        month -= 1
                        if month < 1:
                            month = 12
                            year -= 1
                    month_date = date(year, month, 1)
                
                month_key = month_date.strftime('%Y-%m')
                
                # Query for this specific month
                month_end = (month_date.replace(month=month_date.month % 12 + 1, day=1) - timedelta(days=1)) if month_date.month < 12 else date(month_date.year + 1, 1, 1) - timedelta(days=1)
                
                month_query = db.session.query(
                    func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                    func.count(Invoice.id).label('count')
                ).filter(
                    and_(
                        Invoice.invoice_date >= month_date,
                        Invoice.invoice_date <= month_end
                    )
                ).first()
                
                month_revenue = float(month_query.revenue or 0) if month_query else 0.0
                month_count = month_query.count or 0 if month_query else 0
                
                # Query for collections in this specific month
                month_paid_query = db.session.query(
                    func.coalesce(func.sum(PaymentRecord.total_amount), 0).label('paid')
                ).filter(
                    and_(
                        PaymentRecord.payment_date >= month_date,
                        PaymentRecord.payment_date <= month_end
                    )
                ).first()
                month_paid = float(month_paid_query.paid or 0) if month_paid_query else 0.0
                
                monthly_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'month_key': month_key,
                    'revenue': month_revenue,
                    'paid_revenue': month_paid,
                    'count': month_count
                })
        except Exception as e:
            print(f"DEBUG: Monthly trends error: {e}")
            import traceback
            traceback.print_exc()
            # Generate empty months
            for i in range(11, -1, -1):
                month_date = today.replace(day=1) - timedelta(days=30*i)
                monthly_data.append({
                    'month': month_date.strftime('%b %Y'),
                    'month_key': month_date.strftime('%Y-%m'),
                    'revenue': 0.0,
                    'paid_revenue': 0.0,
                    'count': 0
                })
        
        # 6. DAILY TREND DATA (Last 30 days)
        daily_data = []
        try:
            for i in range(29, -1, -1):
                day_date = today - timedelta(days=i)
                day_start = day_date
                day_end = day_date
                
                day_query = db.session.query(
                    func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                    func.count(Invoice.id).label('count')
                ).filter(
                    Invoice.invoice_date == day_date
                ).first()
                
                day_revenue = float(day_query.revenue or 0) if day_query else 0.0
                day_count = day_query.count or 0 if day_query else 0
                
                # Query for collections on this day
                day_paid_query = db.session.query(
                    func.coalesce(func.sum(PaymentRecord.total_amount), 0).label('paid')
                ).filter(
                    PaymentRecord.payment_date == day_date
                ).first()
                day_paid = float(day_paid_query.paid or 0) if day_paid_query else 0.0
                
                daily_data.append({
                    'day': day_date.strftime('%d %b'),
                    'date': str(day_date),
                    'revenue': day_revenue,
                    'paid_revenue': day_paid,
                    'count': day_count
                })
        except Exception as e:
            print(f"DEBUG: Daily trends error: {e}")
            for i in range(29, -1, -1):
                day_date = today - timedelta(days=i)
                daily_data.append({
                    'day': day_date.strftime('%d %b'),
                    'date': str(day_date),
                    'revenue': 0.0,
                    'paid_revenue': 0.0,
                    'count': 0
                })
        
        # 7. PAYMENT AGING ANALYSIS
        try:
            aging_invoices = db.session.query(
                Invoice.invoice_date,
                Invoice.total_amount
            ).filter(
                Invoice.status.in_(['unpaid', 'partially_paid'])
            ).all()
            
            aging_buckets = defaultdict(lambda: {'count': 0, 'amount': Decimal('0')})
            for inv_date, amount in aging_invoices:
                days_diff = (today - inv_date).days
                if days_diff <= 30:
                    bucket = 'current'
                elif days_diff <= 60:
                    bucket = '30_days'
                elif days_diff <= 90:
                    bucket = '60_days'
                elif days_diff <= 120:
                    bucket = '90_days'
                else:
                    bucket = 'over_90_days'
                
                aging_buckets[bucket]['count'] += 1
                aging_buckets[bucket]['amount'] += amount
            
            aging_query = [
                type('obj', (object,), {
                    'age_bucket': bucket,
                    'count': data['count'],
                    'amount': float(data['amount'])
                })() for bucket, data in aging_buckets.items()
            ]
        except:
            aging_query = []
        
        aging_data = {
            'current': 0,
            '30_days': 0,
            '60_days': 0,
            '90_days': 0,
            'over_90_days': 0
        }
        
        aging_amounts = {
            'current': 0.0,
            '30_days': 0.0,
            '60_days': 0.0,
            '90_days': 0.0,
            'over_90_days': 0.0
        }
        
        for row in aging_query:
            bucket = row.age_bucket
            if bucket in aging_data:
                aging_data[bucket] = row.count
                aging_amounts[bucket] = float(row.amount)
        
        # 8. PRODUCT/ITEM ANALYSIS (optional)
        top_items = []
        if InvoiceItem:
            try:
                item_analysis = db.session.query(
                    InvoiceItem.description,
                    func.sum(InvoiceItem.quantity).label('total_quantity'),
                    func.sum(InvoiceItem.amount).label('total_amount'),
                    func.count(InvoiceItem.id).label('times_sold')
                ).group_by(InvoiceItem.description).order_by(
                    func.sum(InvoiceItem.amount).desc()
                ).limit(10).all()
                
                top_items = [{
                    'description': row.description[:50],
                    'quantity': float(row.total_quantity),
                    'amount': float(row.total_amount),
                    'times_sold': row.times_sold
                } for row in item_analysis]
            except Exception as e:
                print(f"Item analysis failed (non-critical): {e}")
                top_items = []
        
        # 9. COMPANY STATS
        try:
            company_stats = {
                'total_customers': Customer.query.count(),
                'total_vendors': Vendor.query.count() if Vendor else 0,
                'total_purchase_orders': PurchaseOrder.query.count() if PurchaseOrder else 0,
            }
        except:
            company_stats = {
                'total_customers': 0,
                'total_vendors': 0,
                'total_purchase_orders': 0
            }
        
        # 10. QUICK CALCULATIONS
        avg_invoice_value = (total_revenue / total_invoices) if total_invoices > 0 else 0
        
        # 11. YEAR-TO-DATE METRICS
        try:
            ytd_query = db.session.query(
                func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                func.count(Invoice.id).label('count')
            ).filter(
                Invoice.invoice_date >= year_start
            ).first()
            
            ytd_revenue = float(ytd_query.revenue or 0) if ytd_query else 0.0
            ytd_count = ytd_query.count or 0 if ytd_query else 0
        except:
            ytd_revenue = 0.0
            ytd_count = 0
        
        # 12. OVERDUE INVOICES
        try:
            overdue_query = db.session.query(
                func.count(Invoice.id).label('count'),
                func.coalesce(func.sum(Invoice.total_amount), 0).label('amount')
            ).filter(
                and_(
                    Invoice.due_date < today,
                    Invoice.status.in_(['unpaid', 'partially_paid'])
                )
            ).first()
            
            overdue_count = overdue_query.count or 0 if overdue_query else 0
            overdue_amount = float(overdue_query.amount or 0) if overdue_query else 0.0
        except:
            overdue_count = 0
            overdue_amount = 0.0
        
        # 13. RECENT ACTIVITY
        try:
            week_ago = today - timedelta(days=7)
            recent_activity = {
                'invoices_created': Invoice.query.filter(Invoice.created_at >= week_ago).count() if hasattr(Invoice, 'created_at') else 0,
                'customers_added': Customer.query.filter(Customer.created_at >= week_ago).count() if hasattr(Customer, 'created_at') else 0,
            }
        except:
            recent_activity = {
                'invoices_created': 0,
                'customers_added': 0
            }
        
        # 14. WEEKLY BREAKDOWN (Last 8 weeks)
        weekly_data = []
        try:
            for i in range(7, -1, -1):
                week_start_date = today - timedelta(days=today.weekday() + 7*i)
                week_end_date = week_start_date + timedelta(days=6)
                
                week_query = db.session.query(
                    func.coalesce(func.sum(Invoice.total_amount), 0).label('revenue'),
                    func.count(Invoice.id).label('count')
                ).filter(
                    and_(
                        Invoice.invoice_date >= week_start_date,
                        Invoice.invoice_date <= week_end_date
                    )
                ).first()
                
                week_rev = float(week_query.revenue or 0) if week_query else 0.0
                week_cnt = week_query.count or 0 if week_query else 0
                
                # Query for collections this week
                week_paid_query = db.session.query(
                    func.coalesce(func.sum(PaymentRecord.total_amount), 0).label('paid')
                ).filter(
                    and_(
                        PaymentRecord.payment_date >= week_start_date,
                        PaymentRecord.payment_date <= week_end_date
                    )
                ).first()
                week_paid = float(week_paid_query.paid or 0) if week_paid_query else 0.0
                
                weekly_data.append({
                    'week': f"Week {i+1}",
                    'label': week_start_date.strftime('%d %b'),
                    'revenue': week_rev,
                    'paid_revenue': week_paid,
                    'count': week_cnt
                })
        except:
            for i in range(7, -1, -1):
                week_start_date = today - timedelta(days=today.weekday() + 7*i)
                weekly_data.append({
                    'week': f"Week {i+1}",
                    'label': week_start_date.strftime('%d %b'),
                    'revenue': 0.0,
                    'paid_revenue': 0.0,
                    'count': 0
                })
        
        # 15. PERFORMANCE INDICATORS
        payment_collection_rate = (paid_amount / total_revenue * 100) if total_revenue > 0 else 0
        avg_days_to_payment = 0  # Can be calculated from payment history if available
        
        # Compile all dashboard data
        dashboard_data = {
            'revenue_metrics': {
                'total_revenue': total_revenue,
                'total_collected': paid_amount,  # Use existing paid_amount from status breakdown
                'current_month_revenue': current_month_revenue,
                'current_month_collected': current_month_paid,
                'previous_month_revenue': previous_month_revenue,
                'revenue_growth': round(revenue_growth, 2),
                'ytd_revenue': ytd_revenue,
                'avg_invoice_value': round(avg_invoice_value, 2),
                'week_revenue': week_revenue,
                'quarter_revenue': 0.0  # Can be calculated if needed
            },
            'invoice_metrics': {
                'total_invoices': total_invoices,
                'current_month_count': current_month_count,
                'previous_month_count': previous_month_count,
                'invoice_growth': round(invoice_growth, 2),
                'avg_invoice_value': round(avg_invoice_value, 2),
                'ytd_count': ytd_count,
                'week_count': week_count
            },
            'payment_status': {
                'unpaid': {
                    'amount': unpaid_amount,
                    'count': unpaid_count,
                    'percentage': round((unpaid_amount / total_revenue * 100) if total_revenue > 0 else 0, 1)
                },
                'paid': {
                    'amount': paid_amount,
                    'count': paid_count,
                    'percentage': round((paid_amount / total_revenue * 100) if total_revenue > 0 else 0, 1)
                },
                'partially_paid': {
                    'amount': partially_paid_amount,
                    'count': partially_paid_count,
                    'percentage': round((partially_paid_amount / total_revenue * 100) if total_revenue > 0 else 0, 1)
                },
                'outstanding_amount': outstanding_amount,
                'overdue': {
                    'count': overdue_count,
                    'amount': overdue_amount
                },
                'collection_rate': round(payment_collection_rate, 2)
            },
            'gst_breakdown': {
                'total_gst': total_gst,
                'cgst': total_cgst,
                'sgst': total_sgst,
                'igst': total_igst,
                'current_month_gst': current_month_gst
            },
            'top_customers': {
                'by_revenue': top_customers_revenue,
                'by_count': top_customers_count
            },
            'top_items': top_items,
            'monthly_trends': monthly_data,
            'daily_trends': daily_data,
            'weekly_trends': weekly_data,
            'aging_analysis': {
                'counts': aging_data,
                'amounts': aging_amounts
            },
            'company_stats': company_stats,
            'recent_activity': recent_activity,
            'performance_indicators': {
                'collection_rate': round(payment_collection_rate, 2),
                'avg_invoice_value': round(avg_invoice_value, 2),
                'invoice_frequency': round(total_invoices / 12, 2) if total_invoices > 0 else 0
            },
            'quick_stats': {
                'total_revenue_formatted': f"₹{total_revenue:,.2f}",
                'outstanding_amount_formatted': f"₹{outstanding_amount:,.2f}",
                'monthly_revenue_formatted': f"₹{current_month_revenue:,.2f}",
                'overdue_amount_formatted': f"₹{overdue_amount:,.2f}",
                'week_revenue_formatted': f"₹{week_revenue:,.2f}"
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        import traceback
        error_msg = f"Error generating dashboard data: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        # Try to log to Flask logger if available
        try:
            from app import app
            app.logger.error(error_msg)
            app.logger.error(traceback.format_exc())
        except:
            pass
        
        # Return default structure but ensure arrays are populated
        today = date.today()
        empty_monthly = []
        empty_daily = []
        empty_weekly = []
        
        # Generate empty monthly trends (12 months)
        for i in range(11, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30*i)
            empty_monthly.append({
                'month': month_date.strftime('%b %Y'),
                'month_key': month_date.strftime('%Y-%m'),
                'revenue': 0.0,
                'paid_revenue': 0.0,
                'count': 0
            })
        
        # Generate empty daily trends (30 days)
        for i in range(29, -1, -1):
            day_date = today - timedelta(days=i)
            empty_daily.append({
                'day': day_date.strftime('%d %b'),
                'date': str(day_date),
                'revenue': 0.0,
                'paid_revenue': 0.0,
                'count': 0
            })
        
        # Generate empty weekly trends (8 weeks)
        for i in range(7, -1, -1):
            week_start_date = today - timedelta(days=today.weekday() + 7*i)
            empty_weekly.append({
                'week': f"Week {i+1}",
                'label': week_start_date.strftime('%d %b'),
                'revenue': 0.0,
                'paid_revenue': 0.0,
                'count': 0
            })
        
        return {
            'revenue_metrics': {
                'total_revenue': 0, 
                'total_collected': 0,
                'current_month_revenue': 0, 
                'current_month_collected': 0,
                'previous_month_revenue': 0, 
                'revenue_growth': 0, 
                'ytd_revenue': 0, 
                'avg_invoice_value': 0, 
                'week_revenue': 0, 
                'quarter_revenue': 0
            },
            'invoice_metrics': {'total_invoices': 0, 'current_month_count': 0, 'previous_month_count': 0, 'invoice_growth': 0, 'avg_invoice_value': 0, 'ytd_count': 0, 'week_count': 0},
            'payment_status': {'unpaid': {'amount': 0, 'count': 0, 'percentage': 0}, 'paid': {'amount': 0, 'count': 0, 'percentage': 0}, 'partially_paid': {'amount': 0, 'count': 0, 'percentage': 0}, 'outstanding_amount': 0, 'overdue': {'count': 0, 'amount': 0}, 'collection_rate': 0},
            'gst_breakdown': {'total_gst': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'current_month_gst': 0},
            'top_customers': {'by_revenue': [], 'by_count': []},
            'top_items': [],
            'monthly_trends': empty_monthly,
            'daily_trends': empty_daily,
            'weekly_trends': empty_weekly,
            'aging_analysis': {'counts': {'current': 0, '30_days': 0, '60_days': 0, '90_days': 0, 'over_90_days': 0}, 'amounts': {'current': 0, '30_days': 0, '60_days': 0, '90_days': 0, 'over_90_days': 0}},
            'company_stats': {'total_customers': 0, 'total_vendors': 0, 'total_purchase_orders': 0},
            'recent_activity': {'invoices_created': 0, 'customers_added': 0},
            'performance_indicators': {'collection_rate': 0, 'avg_invoice_value': 0, 'invoice_frequency': 0},
            'quick_stats': {'total_revenue_formatted': '₹0.00', 'outstanding_amount_formatted': '₹0.00', 'monthly_revenue_formatted': '₹0.00', 'overdue_amount_formatted': '₹0.00', 'week_revenue_formatted': '₹0.00'}
        }

def format_currency(amount):
    """Format amount as Indian currency"""
    return f"₹{amount:,.2f}"

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)
