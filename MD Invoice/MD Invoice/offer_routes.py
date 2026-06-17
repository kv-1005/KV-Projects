
# Offer Routes

@app.route('/offers')
@login_required
def offers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    customer_filter = request.args.get('customer', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')
    sort_by = request.args.get('sort_by', 'offer_number')
    sort_order = request.args.get('sort_order', 'desc')
    
    query = Offer.query
    
    # helper for search
    if search:
        search_term = f"%{search}%"
        query = query.join(Customer).filter(
            db.or_(
                Offer.offer_number.ilike(search_term),
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.gstin.ilike(search_term)
            )
        )
    
    if status_filter:
        query = query.filter(Offer.status == status_filter)
        
    if customer_filter:
        query = query.filter(Offer.customer_id == customer_filter)
        
    if date_from:
        query = query.filter(Offer.offer_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        
    if date_to:
        query = query.filter(Offer.offer_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        
    if amount_min:
        query = query.filter(Offer.total_amount >= float(amount_min))
        
    if amount_max:
        query = query.filter(Offer.total_amount <= float(amount_max))
        
    # Sorting
    if sort_order == 'asc':
        if sort_by == 'offer_number':
            query = query.order_by(Offer.offer_number.asc())
        elif sort_by == 'date':
            query = query.order_by(Offer.offer_date.asc())
        elif sort_by == 'amount':
            query = query.order_by(Offer.total_amount.asc())
        elif sort_by == 'customer':
            query = query.join(Customer).order_by(Customer.name.asc())
        elif sort_by == 'status':
            query = query.order_by(Offer.status.asc())
    else:
        if sort_by == 'offer_number':
            query = query.order_by(Offer.offer_number.desc())
        elif sort_by == 'date':
            query = query.order_by(Offer.offer_date.desc())
        elif sort_by == 'amount':
            query = query.order_by(Offer.total_amount.desc())
        elif sort_by == 'customer':
            query = query.join(Customer).order_by(Customer.name.desc())
        elif sort_by == 'status':
            query = query.order_by(Offer.status.desc())
            
    # Pagination
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    offers = pagination.items
    
    # Calculate stats for all filtered offers
    all_filtered_offers = query.all()
    
    customers = Customer.query.order_by(Customer.name).all()
    
    return render_template('offers.html', offers=offers, pagination=pagination, 
                         customers=customers, search=search, status_filter=status_filter,
                         customer_filter=customer_filter, date_from=date_from, date_to=date_to,
                         amount_min=amount_min, amount_max=amount_max,
                         sort_by=sort_by, sort_order=sort_order,
                         all_offers=all_filtered_offers)

@app.route('/offers/create', methods=['GET', 'POST'])
@login_required
def create_offer():
    form = OfferForm()
    form.customer_id.choices = [(c.id, f"{c.name} - {c.city}, {c.state}") for c in Customer.query.order_by(Customer.name, Customer.city).all()]
    
    # Populate signature choices
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))
    form.selected_signature.choices = signature_choices
    
    # Generate next offer number
    business_year = get_financial_year_prefix()
    
    existing_offers = Offer.query.filter(
        Offer.offer_number.like(f'QT{business_year}-%')
    ).all()
    
    sequential_numbers = []
    for offer in existing_offers:
        try:
            # Format QT2526-001
            number_part = offer.offer_number.split('-')[-1]
            if number_part.isdigit() and len(number_part) == 3:
                sequential_numbers.append(int(number_part))
        except (IndexError, ValueError):
            continue
            
    if sequential_numbers:
        next_number = max(sequential_numbers) + 1
    else:
        next_number = 1
        
    next_offer_number = f"QT{business_year}-{next_number:03d}"
    
    if request.method == 'GET':
        current_date = datetime.now().strftime('%Y-%m-%d')
        form.offer_date.data = current_date
        # Valid until 30 days
        valid_until = datetime.now() + timedelta(days=30)
        form.valid_until.data = valid_until.strftime('%Y-%m-%d')
        form.offer_number.data = next_offer_number
        
        # Defaults
        form.terms_text.data = 'Validity: 30 Days.\nDelivery: 2-3 Weeks.\nPayment: 100% Advance.'
        form.payment_text.data = 'Payment: 100% against supply.'
        
    if form.validate_on_submit():
        offer_number = form.offer_number.data.strip()
        
        # Check uniqueness
        existing = Offer.query.filter_by(offer_number=offer_number).first()
        if existing:
            flash(f'Offer number "{offer_number}" already exists.', 'error')
            return render_template('create_offer.html', form=form, next_offer_number=next_offer_number, business_year=business_year)
            
        # Date parsing
        try:
            offer_date = datetime.strptime(form.offer_date.data, '%Y-%m-%d').date()
        except ValueError:
             offer_date = datetime.strptime(form.offer_date.data, '%d/%m/%Y').date()
             
        valid_until = None
        if form.valid_until.data:
            try:
                valid_until = datetime.strptime(form.valid_until.data, '%Y-%m-%d').date()
            except ValueError:
                valid_until = datetime.strptime(form.valid_until.data, '%d/%m/%Y').date()
                
        company = Company.query.first()
        if not company:
            flash('Company details missing.', 'error')
            return redirect(url_for('company'))
            
        meta = {
            'reference_no': form.reference_no.data or '-',
            'subject': form.subject.data or '',
            'terms_text': form.terms_text.data or '',
            'payment_text': form.payment_text.data or '',
            'main_address': form.main_address.data,
            'branch_address': form.branch_address.data
        }
        
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except:
                selected_signature_id = None
                
        offer = Offer(
            offer_number=offer_number,
            customer_id=form.customer_id.data,
            offer_date=offer_date,
            valid_until=valid_until,
            shipping_charges=form.shipping_charges.data or 0,
            notes=json.dumps(meta),
            subtotal=0,
            total_amount=0,
            selected_signature_id=selected_signature_id,
            require_digital_signature=form.require_digital_signature.data,
            status='draft',
            subject=form.subject.data
        )
        
        db.session.add(offer)
        db.session.commit()
        
        log_activity(
            action_type='create',
            entity_type='offer',
            entity_id=offer.id,
            resource_identifier=offer.offer_number,
            description=f"Created offer: {offer.offer_number}"
        )
        
        flash('Offer created! Add items now.', 'success')
        return redirect(url_for('edit_offer', offer_id=offer.id))
        
    return render_template('create_offer.html', form=form, next_offer_number=next_offer_number, business_year=business_year)

@app.route('/offers/<int:offer_id>')
@login_required
def view_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    meta = {}
    if offer.notes:
        try:
            meta = json.loads(offer.notes)
        except:
            meta = {}
    return render_template('view_offer.html', offer=offer, meta=meta)

@app.route('/offers/<int:offer_id>/edit')
@login_required
def edit_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    meta = json.loads(offer.notes) if offer.notes else {}
    
    items_data = []
    for item in offer.items:
        items_data.append({
            'id': item.id,
            'description': item.description,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount),
            'hsn_code': item.hsn_code,
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value)
        })
        
    return render_template('edit_offer.html', offer=offer, items_json=json.dumps(items_data), meta=meta)

@app.route('/offers/<int:offer_id>/edit/details', methods=['GET', 'POST'])
@login_required
def edit_offer_details(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    form = OfferForm()
    
    form.customer_id.choices = [(c.id, f"{c.name} - {c.city}, {c.state}") for c in Customer.query.order_by(Customer.name, Customer.city).all()]
    
    user_signatures = UserSignature.query.filter_by(user_id=current_user.id).order_by(UserSignature.is_default.desc(), UserSignature.created_at.desc()).all()
    signature_choices = [(sig.id, f"{sig.signature_name}{' (Default)' if sig.is_default else ''}") for sig in user_signatures]
    signature_choices.insert(0, ('', 'No Signature'))
    form.selected_signature.choices = signature_choices
    
    try:
        meta = json.loads(offer.notes) if offer.notes else {}
    except:
        meta = {}
        
    if request.method == 'GET':
        form.customer_id.data = offer.customer_id
        form.offer_date.data = offer.offer_date.strftime('%Y-%m-%d') if offer.offer_date else ''
        form.valid_until.data = offer.valid_until.strftime('%Y-%m-%d') if offer.valid_until else ''
        form.offer_number.data = offer.offer_number
        form.shipping_charges.data = float(offer.shipping_charges or 0)
        form.reference_no.data = meta.get('reference_no') or '-'
        form.subject.data = meta.get('subject') or offer.subject or ''
        form.terms_text.data = meta.get('terms_text') or ''
        form.payment_text.data = meta.get('payment_text') or ''
        form.main_address.data = meta.get('main_address') or 'salem'
        form.branch_address.data = meta.get('branch_address') or 'chennai'
        form.selected_signature.data = str(offer.selected_signature_id or '')
        form.require_digital_signature.data = offer.require_digital_signature
        
    if form.validate_on_submit():
        new_offer_number = form.offer_number.data.strip()
        existing = Offer.query.filter(Offer.offer_number == new_offer_number, Offer.id != offer.id).first()
        if existing:
            flash(f'Offer number "{new_offer_number}" exists.', 'error')
            return render_template('edit_offer_details.html', form=form, offer=offer) 
            
        try:
            offer_date = datetime.strptime(form.offer_date.data, '%Y-%m-%d').date()
        except:
            offer_date = None
            
        try:
            valid_until = datetime.strptime(form.valid_until.data, '%Y-%m-%d').date()
        except:
             valid_until = None
             
        updated_meta = {
            'reference_no': form.reference_no.data or '-',
            'subject': form.subject.data or '',
            'terms_text': form.terms_text.data or '',
            'payment_text': form.payment_text.data or '',
            'main_address': form.main_address.data,
            'branch_address': form.branch_address.data
        }
        
        selected_signature_id = None
        if form.selected_signature.data and form.selected_signature.data != '':
            try:
                selected_signature_id = int(form.selected_signature.data)
            except:
                selected_signature_id = None
        
        offer.offer_number = new_offer_number
        offer.customer_id = form.customer_id.data
        offer.offer_date = offer_date
        offer.valid_until = valid_until
        offer.shipping_charges = form.shipping_charges.data or 0
        offer.notes = json.dumps(updated_meta)
        offer.selected_signature_id = selected_signature_id
        offer.require_digital_signature = form.require_digital_signature.data
        offer.subject = form.subject.data
        
        db.session.commit()
        flash('Offer updated.', 'success')
        return redirect(url_for('edit_offer', offer_id=offer.id))
        
    # We must clone edit_invoice_details -> edit_offer_details. I'll do that separately.
    return render_template('edit_offer_details.html', form=form, offer=offer)

@app.route('/offers/<int:offer_id>/delete', methods=['POST'])
@login_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    try:
        for item in offer.items:
            db.session.delete(item)
        db.session.delete(offer)
        db.session.commit()
        flash('Offer deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('offers'))

@app.route('/offers/<int:offer_id>/print')
@login_required
def offer_print(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    company = Company.query.first()
    
    if not offer.items:
        flash('No items in offer.', 'error')
        return redirect(url_for('edit_offer', offer_id=offer_id))
        
    if not company:
        flash('Company setup required.', 'error')
        return redirect(url_for('company'))
        
    company_details = get_company_details()
    company_state = get_state_from_gstin(company_details['gstin'])
    
    if not offer.customer.gstin:
        # Flash but continue? Invoice print forces redirect.
         pass # Allow without GSTIN for offer? Just warn.
         # Actually invoice code redirects. But offers are proposals. Let's redirect if critical or handle gracefully.
         # For consistency with invoice, let's redirect.
         pass 

    customer_state = get_state_from_gstin(offer.customer.gstin) if offer.customer.gstin else company_state # Fallback
    is_interstate = customer_state != company_state
    
    from decimal import Decimal
    
    item_details = []
    for item in offer.items:
        gross = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        validated_discount = validate_discount_value(item.discount_type, item.discount_value, gross)
        
        if item.discount_type == 'percentage':
            discount = gross * validated_discount / Decimal('100')
        elif item.discount_type == 'amount':
            discount = validated_discount
        else:
            discount = Decimal('0')
            
        taxable = max(gross - discount, Decimal('0'))
        cgst, sgst, igst = calculate_gst(taxable, item.tax_rate, is_interstate)
        total = taxable + cgst + sgst + igst
        
        item_details.append({
            'item': item,
            'discount': float(discount),
            'taxable': float(taxable),
            'cgst': float(cgst),
            'sgst': float(sgst),
            'igst': float(igst),
            'total': float(total)
        })
        
    logo_path = url_for('static', filename='uploads/md_logo.jpg')
    signature_data = offer.selected_signature.signature_data if offer.selected_signature else None
    
    return render_template('print_offer.html',
                         offer=offer,
                         company=company,
                         logo_path=logo_path,
                         float=float,
                         number_to_words=number_to_words,
                         item_details=item_details,
                         is_interstate=is_interstate,
                         company_details=company_details,
                         signature_data=signature_data)

@app.route('/api/offers/<int:offer_id>/items', methods=['POST'])
@login_required
def add_offer_item(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json()
    
    description = data.get('description')
    hsn_code = data.get('hsn_code', '85044090')
    quantity = Decimal(str(data.get('quantity', 0)))
    unit_price = Decimal(str(data.get('unit_price', 0)))
    tax_rate = Decimal(str(data.get('tax_rate', 18)))
    discount_type = data.get('discount_type', 'amount')
    discount_value = Decimal(str(data.get('discount_value', 0)))
    
    if not description or quantity <= 0:
        return jsonify({'error': 'Invalid data'}), 400
        
    gross = quantity * unit_price
    validated_discount = validate_discount_value(discount_type, discount_value, gross)
    
    if discount_type == 'percentage':
        discount_amt = gross * validated_discount / Decimal('100')
    elif discount_type == 'amount':
        discount_amt = validated_discount
    else:
        discount_amt = Decimal('0')
        
    amount = max(gross - discount_amt, Decimal('0'))
    
    item = OfferItem(
        offer_id=offer_id,
        description=description,
        hsn_code=hsn_code,
        quantity=quantity,
        unit_price=unit_price,
        discount_type=discount_type,
        discount_value=validated_discount,
        tax_rate=tax_rate,
        amount=amount
    )
    
    db.session.add(item)
    db.session.commit()
    
    update_offer_totals_inline(offer)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'description': item.description,
            'hsn_code': item.hsn_code,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount_type': item.discount_type,
            'discount_value': float(item.discount_value),
            'tax_rate': float(item.tax_rate),
            'amount': float(item.amount)
        }
    })

@app.route('/api/offers/<int:offer_id>/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_offer_item(offer_id, item_id):
    offer = Offer.query.get_or_404(offer_id)
    item = OfferItem.query.filter_by(id=item_id, offer_id=offer_id).first_or_404()
    db.session.delete(item)
    
    if offer.items:
        update_offer_totals_inline(offer)
    else:
        offer.subtotal = 0
        offer.cgst_amount = 0
        offer.sgst_amount = 0
        offer.igst_amount = 0
        offer.total_amount = 0
        
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/offers/<int:offer_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_offer_item(offer_id, item_id):
    offer = Offer.query.get_or_404(offer_id)
    item = OfferItem.query.filter_by(id=item_id, offer_id=offer_id).first_or_404()
    data = request.get_json()
    
    item.description = data.get('description', item.description)
    item.hsn_code = data.get('hsn_code', item.hsn_code)
    item.quantity = Decimal(str(data.get('quantity', item.quantity)))
    item.unit_price = Decimal(str(data.get('unit_price', item.unit_price)))
    item.tax_rate = Decimal(str(data.get('tax_rate', item.tax_rate)))
    item.discount_type = data.get('discount_type', item.discount_type)
    item.discount_value = Decimal(str(data.get('discount_value', item.discount_value)))
    
    gross = item.quantity * item.unit_price
    validated_discount = validate_discount_value(item.discount_type, item.discount_value, gross)
    item.discount_value = validated_discount
    
    if item.discount_type == 'percentage':
        discount_amt = gross * validated_discount / Decimal('100')
    elif item.discount_type == 'amount':
        discount_amt = validated_discount
    else:
        discount_amt = Decimal('0')
        
    item.amount = max(gross - discount_amt, Decimal('0'))
    
    update_offer_totals_inline(offer)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/offers/<int:offer_id>/status', methods=['POST'])
@login_required
def update_offer_status(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json()
    status = data.get('status')
    if status in ['draft', 'sent', 'accepted', 'rejected']:
        offer.status = status
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/api/offers/<int:offer_id>/settings', methods=['POST'])
@login_required
def update_offer_settings(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json()
    offer.shipping_charges = Decimal(str(data.get('shipping_charges', 0)))
    
    meta = json.loads(offer.notes) if offer.notes else {}
    meta['reference_no'] = data.get('reference_no', '-')
    offer.notes = json.dumps(meta)
    
    update_offer_totals_inline(offer)
    db.session.commit()
    return jsonify({'success': True})

def update_offer_totals_inline(offer):
    # Recalculate totals
    subtotal = Decimal('0')
    cgst_total = Decimal('0')
    sgst_total = Decimal('0')
    igst_total = Decimal('0')
    
    company = Company.query.first()
    company_state = get_state_from_gstin(company.gstin) if company and company.gstin else ''
    customer_state = get_state_from_gstin(offer.customer.gstin) if offer.customer and offer.customer.gstin else ''
    is_interstate = company_state != customer_state
    
    for item in offer.items:
        subtotal += item.amount
        cgst, sgst, igst = calculate_gst(item.amount, item.tax_rate, is_interstate)
        cgst_total += cgst
        sgst_total += sgst
        igst_total += igst
        
    offer.subtotal = subtotal
    offer.cgst_amount = cgst_total
    offer.sgst_amount = sgst_total
    offer.igst_amount = igst_total
    offer.total_amount = subtotal + cgst_total + sgst_total + igst_total + offer.shipping_charges
