
$file = "g:\MD Invoice\templates\edit_offer_details.html"
$content = Get-Content $file -Raw
$content = $content -replace "Invoice", "Offer"
$content = $content -replace "invoice", "offer"
$content = $content -replace "Offers", "Offers" 
# Fix plural if needed, but simple replacement might affect "Invoices" -> "Offerss" if I replaced "Invoice" -> "Offer" first.
# "Invoices" -> "Offers" (if I change Invoice->Offer, Invoices became Offerss).
# Better to be specific.

# Reset content
$content = Get-Content $file -Raw

# Specific replacements
$content = $content.Replace("Edit Invoice", "Edit Offer")
$content = $content.Replace("invoice.id", "offer.id")
$content = $content.Replace("url_for('edit_invoice'", "url_for('edit_offer'")
$content = $content.Replace("url_for('invoices')", "url_for('offers')")
$content = $content.Replace("Invoice Details", "Offer Details")
$content = $content.Replace("Invoice Number", "Offer Number")
$content = $content.Replace("invoice_number", "offer_number")
$content = $content.Replace("invoice_date", "offer_date")
$content = $content.Replace("due_date", "valid_until") # Mapping due_date to valid_until
$content = $content.Replace("Due Date", "Valid Until")

Set-Content $file $content
Write-Host "Processed $file"
