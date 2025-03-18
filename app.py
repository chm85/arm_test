from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
import json
import datetime
import uuid
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Azure Storage Configuration
AZURE_STORAGE_ACCOUNT_NAME = "hackathon1march2sa"
AZURE_STORAGE_CONTAINER = "inbound"
AZURE_KEY = os.getenv("SAKEY")
AZURE_STORAGE_CONNECTION_STRING = f"DefaultEndpointsProtocol=https;AccountName=hackathon1march2sa;AccountKey={AZURE_KEY};EndpointSuffix=core.windows.net"

# Define the form
class ARMTemplateForm(FlaskForm):
    app_name = StringField('App Name')
    long_app_name = StringField('Long App Name')
    environment = SelectField('Environment', choices=[('dev', 'Development'), ('prod', 'Production')])
    hardware_specs = SelectField('Hardware Specs', choices=[('basic', 'Basic'), ('high', 'High Performance')])
    data_classification = SelectField('Data Classification', choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    compliance_pci = BooleanField('PCI Compliance')
    compliance_gdpr = BooleanField('GDPR Compliance')
    business_owner = StringField('Business Owner')
    criticality = SelectField('Criticality', choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    admin_pass = StringField('Admin Password')
    submit = SubmitField('Generate ARM Template')

# Function to generate filename
def generate_filename():
    today = datetime.datetime.now().strftime('%Y_%m_%d')
    unique_id = str(uuid.uuid4())[:7]
    return f"{today}_ARM_{unique_id}.json"

# Function to upload JSON to Azure Blob Storage
def upload_to_azure(blob_name, json_data):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=AZURE_STORAGE_CONTAINER, blob=f"inbound/{blob_name}")

        # Upload JSON content
        blob_client.upload_blob(json.dumps(json_data, indent=4), overwrite=True)
        print(f"Uploaded {blob_name} to Azure Storage in inbound folder.")

        return True
    except Exception as e:
        print(f"Error uploading to Azure: {e}")
        return False

# Function to update and upload ARM template
def update_and_save_template(form_data):
    with open("templates/arm_template.json", "r") as file:
        template = json.load(file)

    # Modify the template based on form input
    template["parameters"]["appName"]["value"] = form_data["app_name"]
    template["parameters"]["longAppName"]["value"] = form_data["long_app_name"]
    template["parameters"]["environment"]["value"] = form_data["environment"]
    template["parameters"]["hardwareSpecs"]["value"] = form_data["hardware_specs"]
    template["parameters"]["dataClassification"]["value"] = form_data["data_classification"]
    template["parameters"]["compliancePCI"]["value"] = form_data["compliance_pci"]
    template["parameters"]["complianceGDPR"]["value"] = form_data["compliance_gdpr"]
    template["parameters"]["businessOwner"]["value"] = form_data["business_owner"]
    template["parameters"]["criticality"]["value"] = form_data["criticality"]
    template["parameters"]["adminPass"]["value"] = form_data["admin_pass"]

    filename = generate_filename()
    
    # Upload the file to Azure Storage
    success = upload_to_azure(filename, template)

    return filename if success else None

@app.route("/", methods=["GET", "POST"])
def index():
    form = ARMTemplateForm()
    if form.validate_on_submit():
        form_data = {
            "app_name": form.app_name.data,
            "long_app_name": form.long_app_name.data,
            "environment": form.environment.data,
            "hardware_specs": form.hardware_specs.data,
            "data_classification": form.data_classification.data,
            "compliance_pci": form.compliance_pci.data,
            "compliance_gdpr": form.compliance_gdpr.data,
            "business_owner": form.business_owner.data,
            "criticality": form.criticality.data,
            "admin_pass": form.admin_pass.data,
        }
        filename = update_and_save_template(form_data)

        if filename:
            return redirect(url_for("success", filename=filename))
        else:
            return "Error uploading file to Azure", 500
    
    return render_template("index.html", form=form)

@app.route("/success/<filename>")
def success(filename):
    return render_template("success.html", filename=filename)

if __name__ == "__main__":
    app.run(debug=True)
