import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="Solar Efficiency Analyzer", page_icon="🔆")

st.title("🔆 Solar Plant Efficiency Analyzer")

# Sidebar metadata inputs
with st.sidebar:
    st.header("Project Info")
    plant_name = st.text_input("Solar Plant Name")
    project_code = st.text_input("Project Code")
    address = st.text_area("Address")

    st.header("Panel Configuration")
    panel_power = st.number_input("Solar Panel Power (W)", min_value=1, value=400)
    efficiency = st.number_input("Panel Efficiency (%)", min_value=0.0, max_value=100.0, value=18.0)
    num_panels = st.number_input("Number of Panels", min_value=1, value=10)

    st.markdown("#### Panel Dimensions")
    length = st.number_input("Length (m)", min_value=0.1, value=1.6)
    width = st.number_input("Width (m)", min_value=0.1, value=1.0)

panel_area = length * width  # Compute area dynamically

# File uploads
irradiance_file = st.file_uploader("☀️ Upload Irradiance Data CSV", type="csv")
generation_file = st.file_uploader("⚡ Upload Actual Generation Data CSV", type="csv")

# Report generation trigger (single button)
if st.button("📝 Generate Report"):
    if irradiance_file and generation_file:
        try:
            irradiance_df = pd.read_csv(irradiance_file)
            generation_df = pd.read_csv(generation_file)

            if "Month" not in irradiance_df.columns or "Month" not in generation_df.columns:
                st.error("Both CSVs must include a 'Month' column.")
            else:
                df = pd.merge(irradiance_df, generation_df, on="Month")
                df["ExpectedGeneration"] = (efficiency / 100) * num_panels * panel_area * df["Irradiance"]
                df["MonthlyEfficiency"] = (df["ActualGeneration"] / df["ExpectedGeneration"]) * 100

                total_expected = df["ExpectedGeneration"].sum()
                total_actual = df["ActualGeneration"].sum()
                overall_eff = (total_actual / total_expected) * 100

                # Plotting
                st.subheader("📊 Efficiency Visualization")
                fig, ax = plt.subplots(figsize=(10, 5))

                # Expected Generation (Dark Blue)
                ax.bar(df["Month"], df["ExpectedGeneration"], color='darkblue', label="Expected", alpha=0.6)

                # Actual Generation (Green to Red gradient based on MonthlyEfficiency)
                for i, row in df.iterrows():
                    color = plt.cm.RdYlGn_r(np.clip(row["MonthlyEfficiency"] / 100, 0, 1))
                    ax.bar(row["Month"], row["ActualGeneration"], color=color, alpha=0.8)

                ax.set_ylabel("Energy (kWh)")
                ax.set_title("Expected vs Actual Monthly Generation")
                ax.grid(True)

                # Labels
                for i, row in df.iterrows():
                    ax.text(row["Month"], row["ExpectedGeneration"] + 2, f"{row['ExpectedGeneration']:.2f}", color='black', ha='center')
                    ax.text(row["Month"], row["ActualGeneration"] + 2, f"{row['ActualGeneration']:.2f}", color='red', ha='center')

                # Legend
                ax.legend(loc="upper left")

                st.pyplot(fig)

                # Monthly Efficiency Plot
                st.subheader("📈 Monthly Efficiency")
                fig_eff, ax_eff = plt.subplots(figsize=(10, 5))
                ax_eff.plot(df["Month"], df["MonthlyEfficiency"], marker='o', color='purple', label="Efficiency (%)")
                ax_eff.set_ylabel("Efficiency (%)")
                ax_eff.set_title("Monthly Efficiency")
                ax_eff.grid(True)
                ax_eff.legend()

                st.pyplot(fig_eff)

                # Generate PDF Report
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=A4)
                width, height = A4

                y = height - 40
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "Solar Efficiency Report")
                y -= 30

                c.setFont("Helvetica", 11)
                c.drawString(50, y, f"Plant Name: {plant_name}")
                y -= 15
                c.drawString(50, y, f"Project Code: {project_code}")
                y -= 15
                c.drawString(50, y, f"Address: {address}")
                y -= 30

                c.drawString(50, y, f"Panel Power: {panel_power} W")
                y -= 15
                c.drawString(50, y, f"Panel Efficiency: {efficiency}%")
                y -= 15
                c.drawString(50, y, f"Number of Panels: {num_panels}")
                y -= 15
                c.drawString(50, y, f"Panel Area: {panel_area:.2f} m²")
                y -= 30

                c.drawString(50, y, f"Total Expected Generation: {total_expected:.2f} kWh")
                y -= 15
                c.drawString(50, y, f"Total Actual Generation: {total_actual:.2f} kWh")
                y -= 15
                c.drawString(50, y, f"Overall Efficiency: {overall_eff:.2f}%")
                y -= 30

                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Monthly Details:")
                y -= 20
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "Month | Irradiance | Expected | Actual | Efficiency")
                y -= 15
                c.line(50, y, 550, y)
                y -= 10

                for _, row in df.iterrows():
                    line = f"{row['Month']:5} | {row['Irradiance']:10.1f} | {row['ExpectedGeneration']:8.1f} | {row['ActualGeneration']:8.1f} | {row['MonthlyEfficiency']:8.1f}%"
                    c.drawString(50, y, line)
                    y -= 15
                    if y < 100:
                        c.showPage()
                        y = height - 50

                # Add the graphs as images
                img_path = "/tmp/solar_generation_chart.png"
                fig.savefig(img_path)
                c.drawImage(img_path, 50, y-400, width=500, height=300)
                y -= 400

                img_path_eff = "/tmp/efficiency_chart.png"
                fig_eff.savefig(img_path_eff)
                c.drawImage(img_path_eff, 50, y-400, width=500, height=300)
                y -= 400

                c.save()
                pdf_data = pdf_buffer.getvalue()
                st.success("✅ Report generated successfully!")

                # PDF download
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_data,
                    file_name="solar_efficiency_report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Error processing files: {e}")
    else:
        st.warning("Please upload both CSV files to proceed.")
