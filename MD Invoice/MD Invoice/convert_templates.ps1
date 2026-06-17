$files = @(
    "g:\MD Invoice\templates\print_offer.html",
    "g:\MD Invoice\templates\create_offer.html",
    "g:\MD Invoice\templates\offers.html",
    "g:\MD Invoice\templates\edit_offer.html",
    "g:\MD Invoice\templates\view_offer.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        
        # Text Replacements (Visual)
        $content = $content -replace 'TAX INVOICE', 'QUOTATION'
        $content = $content -replace 'Tax Invoice', 'Quotation'
        $content = $content -replace 'Invoice No\.', 'Offer No.'
        $content = $content -replace 'Invoice Date', 'Offer Date'
        $content = $content -replace 'Due Date', 'Valid Until'
        $content = $content -replace 'Invoice List', 'Offer List'
        $content = $content -replace 'Create Invoice', 'Create Offer'
        $content = $content -replace 'Edit Invoice', 'Edit Offer'
        $content = $content -replace 'View Invoice', 'View Offer'
        $content = $content -replace 'Delete Invoice', 'Delete Offer'
        $content = $content -replace 'Invoices', 'Offers' # Careful, might hit routes too, which is good
        
        # Variable/Code Replacements
        $content = $content -replace 'invoice\.invoice_number', 'offer.offer_number'
        $content = $content -replace 'invoice\.invoice_date', 'offer.offer_date'
        $content = $content -replace 'invoice\.due_date', 'offer.valid_until'
        $content = $content -replace 'invoice\.customer', 'offer.customer'
        $content = $content -replace 'invoice\.total_amount', 'offer.total_amount'
        $content = $content -replace 'invoice\.subtotal', 'offer.subtotal'
        $content = $content -replace 'invoice\.cgst_amount', 'offer.cgst_amount'
        $content = $content -replace 'invoice\.sgst_amount', 'offer.sgst_amount'
        $content = $content -replace 'invoice\.igst_amount', 'offer.igst_amount'
        $content = $content -replace 'invoice\.shipping_charges', 'offer.shipping_charges'
        $content = $content -replace 'invoice\.status', 'offer.status'
        $content = $content -replace 'invoice\.items', 'offer.items'
        $content = $content -replace 'invoice\.notes', 'offer.notes'
        $content = $content -replace 'invoice\.id', 'offer.id'
        
        $content = $content -replace 'invoice_id', 'offer_id'
        $content = $content -replace 'invoices\.html', 'offers.html'
        
        # General variable replacement (careful with this one)
        # Replacing 'invoice' with 'offer' where it looks like a variable
        $content = $content -replace 'invoice ', 'offer '
        $content = $content -replace 'invoice\.', 'offer.'
        
        # Routes
        $content = $content -replace 'url_for\(''invoices''', 'url_for(''offers'''
        $content = $content -replace 'url_for\(''create_invoice''', 'url_for(''create_offer'''
        $content = $content -replace 'url_for\(''edit_invoice''', 'url_for(''edit_offer'''
        $content = $content -replace 'url_for\(''view_invoice''', 'url_for(''view_offer'''
        $content = $content -replace 'url_for\(''invoice_print''', 'url_for(''offer_print'''
        $content = $content -replace 'url_for\(''delete_invoice''', 'url_for(''delete_offer'''
        
        # Specific fixes
        $content = $content -replace 'next_invoice_number', 'next_offer_number'
        
        Set-Content $file $content
        Write-Host "Processed $file"
    } else {
        Write-Host "File not found: $file"
    }
}
