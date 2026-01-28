"""
Test script to send an invoice email using the Sellsy /email/send API
"""
import os
import sys
from src.sellsy_client_v2 import SellsyClientV2

def test_send_invoice_email(invoice_id: int):
    """Test sending invoice email using Sellsy /email/send API"""

    sellsy = SellsyClientV2(
        client_id=os.environ['SELLSY_V2_CLIENT_ID'],
        client_secret=os.environ['SELLSY_V2_CLIENT_SECRET']
    )

    print(f"\n{'='*60}")
    print(f"Testing email sending for invoice ID: {invoice_id}")
    print(f"{'='*60}\n")

    # Step 1: Get invoice details
    print("Step 1: Fetching invoice details")
    print("-" * 40)
    try:
        result = sellsy._make_request('GET', f"/invoices/{invoice_id}")
        invoice = result.get('data', {})
        print(f"✅ Invoice found: {invoice.get('reference')}")
        print(f"   Status: {invoice.get('status')}")
        print(f"   Subject: {invoice.get('subject')}")

        # Display client info
        related = invoice.get('related', [])
        if related:
            client = related[0]
            print(f"   Client Type: {client.get('type')}")
            print(f"   Client ID: {client.get('id')}")

    except Exception as e:
        print(f"❌ Failed to get invoice: {str(e)}")
        return

    print()

    # Step 2: Send email using the new method
    print("Step 2: Sending invoice email via /email/send API")
    print("-" * 40)
    try:
        result = sellsy.send_invoice_email(invoice_id)
        print(f"\n✅ SUCCESS! Email sent successfully!")

        # Display results
        data = result.get('data', {})
        print(f"\n📊 Email Details:")
        print(f"   Email ID: {data.get('id')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Subject: {data.get('subject')}")
        print(f"   Created: {data.get('created')}")

        # Display recipients
        to = data.get('to', [])
        if to:
            print(f"\n📧 Recipients:")
            for recipient in to:
                print(f"   - {recipient.get('name')} <{recipient.get('email')}>")

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n{'='*60}")
    print("✅ Test completed successfully!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_send_invoice_email.py <invoice_id>")
        print("Example: python test_send_invoice_email.py 3105")
        sys.exit(1)

    invoice_id = int(sys.argv[1])
    test_send_invoice_email(invoice_id)
