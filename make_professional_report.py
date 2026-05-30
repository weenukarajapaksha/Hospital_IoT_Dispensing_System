from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape


OUT = Path("Hospital_IoT_Dispensing_System_Report.docx")


def safe_text(text):
    return escape(str(text)).replace("\n", "<w:br/>")


def run_text(text, bold=False, italic=False, size=22, color=None, font="Calibri"):
    props = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>', f'<w:sz w:val="{size}"/>']
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    return f"<w:r><w:rPr>{''.join(props)}</w:rPr><w:t xml:space=\"preserve\">{safe_text(text)}</w:t></w:r>"


def paragraph(text="", style=None, align=None, bold=False, italic=False, size=22, color=None, font="Calibri"):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr_xml}{run_text(text, bold, italic, size, color, font)}</w:p>"


def heading(text, level=1):
    style = "Heading1" if level == 1 else "Heading2"
    return paragraph(text, style=style)


def bullet(text):
    return (
        '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/>'
        '<w:numId w:val="1"/></w:numPr></w:pPr>'
        f"{run_text(text)}</w:p>"
    )


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def code_block(title, code):
    parts = [paragraph(title, bold=True)]
    for line in code.splitlines():
        parts.append(paragraph(line[:150], size=18, font="Consolas"))
    return "".join(parts)


def table(headers, rows, widths=None):
    if widths is None:
        widths = [2400] * len(headers)
    tbl = [
        '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
        '<w:tblW w:w="0" w:type="auto"/>'
        '<w:tblLook w:val="04A0"/></w:tblPr><w:tblGrid>'
    ]
    for width in widths:
        tbl.append(f'<w:gridCol w:w="{width}"/>')
    tbl.append("</w:tblGrid>")

    def row(cells, header=False):
        xml = ["<w:tr>"]
        for cell in cells:
            shade = '<w:shd w:fill="D9EAF7"/>' if header else ""
            xml.append(
                f'<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/>{shade}</w:tcPr>'
                f'{paragraph(cell, bold=header, size=20)}</w:tc>'
            )
        xml.append("</w:tr>")
        return "".join(xml)

    tbl.append(row(headers, True))
    for r in rows:
        tbl.append(row(r, False))
    tbl.append("</w:tbl>")
    return "".join(tbl)


def document_xml(body):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
 <w:body>{body}
  <w:sectPr>
   <w:pgSz w:w="11906" w:h="16838"/>
   <w:pgMar w:top="1440" w:right="1080" w:bottom="1080" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>
  </w:sectPr>
 </w:body>
</w:document>'''


styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
 <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
  <w:name w:val="Normal"/><w:qFormat/>
  <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr>
  <w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr>
 </w:style>
 <w:style w:type="paragraph" w:styleId="Title">
  <w:name w:val="Title"/><w:qFormat/>
  <w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr>
  <w:rPr><w:b/><w:rFonts w:ascii="Calibri Light" w:hAnsi="Calibri Light"/><w:sz w:val="40"/><w:color w:val="1F4E79"/></w:rPr>
 </w:style>
 <w:style w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
  <w:pPr><w:spacing w:before="360" w:after="160"/><w:outlineLvl w:val="0"/></w:pPr>
  <w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="1F4E79"/></w:rPr>
 </w:style>
 <w:style w:type="paragraph" w:styleId="Heading2">
  <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
  <w:pPr><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="1"/></w:pPr>
  <w:rPr><w:b/><w:sz w:val="25"/><w:color w:val="2F75B5"/></w:rPr>
 </w:style>
 <w:style w:type="table" w:styleId="TableGrid">
  <w:name w:val="Table Grid"/><w:basedOn w:val="TableNormal"/><w:uiPriority w:val="59"/><w:qFormat/>
  <w:tblPr><w:tblBorders>
   <w:top w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
   <w:left w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
   <w:bottom w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
   <w:right w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
   <w:insideH w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
   <w:insideV w:val="single" w:sz="4" w:space="0" w:color="9E9E9E"/>
  </w:tblBorders></w:tblPr>
 </w:style>
</w:styles>'''


numbering_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
 <w:abstractNum w:abstractNumId="0">
  <w:multiLevelType w:val="hybridMultilevel"/>
  <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
 </w:abstractNum>
 <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>'''


content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
 <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
 <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
 <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
 <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
 <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''


core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <dc:title>IoT Based Chemical Dispensing and Refill System Report</dc:title>
 <dc:creator>Weenuka</dc:creator>
 <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
</cp:coreProperties>'''


app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
 <Application>Microsoft Word</Application>
</Properties>'''


def build_body():
    p = []
    p.append(paragraph("IoT Based Chemical Dispensing and Automatic Refill System", style="Title"))
    p.append(paragraph("Professional Project Report", align="center", bold=True, size=28))
    p.append(paragraph("Simulation Platform: Wokwi with PlatformIO and ESP32", align="center", size=22))
    p.append(paragraph("Prepared for: Hospital chemical dispensing automation project", align="center"))
    p.append(paragraph("Date: May 2026", align="center"))
    p.append(page_break())

    p.append(heading("Executive Summary", 1))
    p.append(paragraph("This report proposes and documents an IoT based automatic chemical dispensing refill system for hospital premises. Each dispensing tank is fitted with only one low-level sensor. When the chemical level falls below the minimum permitted volume, the tank controller sends a refill request to a central controller. The supply system then dispenses a pre-determined volume of chemical mixture into that tank. Since no continuous level sensor is available in the dispensing tank, the final refilled level is controlled by the volume discharged, measured using flow meters."))
    p.append(paragraph("Only one dispensing tank is refilled at any time. If multiple tanks request service, the central controller places the requests in a first-request-first-serve queue. The chemical pump is driven using PWM, but because PWM duty cycle does not guarantee accurate flow, a flow meter is used as the feedback measurement for actual discharged volume. The concentrated chemical supply tank does not contain an internal level sensor; remaining chemical volume is estimated computationally using cumulative measured flow and reconciliation during container replacement."))

    p.append(heading("Table of Contents", 1))
    toc = [
        "Chapter 1: Level Measurement and Chemical Estimation Methods",
        "Chapter 2: Component Selection and Market Product Evaluation",
        "Chapter 3: Failure Detection and Fail-Safe Methods",
        "Chapter 4: Data Collection and Communication Methods",
        "Chapter 5: Complete System Schematic Block Diagram",
        "Chapter 6: Controller and Sensor Schematic Diagram",
        "Chapter 7: Operational Algorithms and State Diagrams",
        "Chapter 8: Wokwi Simulation and Source Code Attachment",
        "Appendix A: Source Code",
        "References",
    ]
    for item in toc:
        p.append(bullet(item))
    p.append(page_break())

    p.append(heading("Chapter 1: Level Measurement and Chemical Estimation Methods", 1))
    p.append(paragraph("The project constraints require a different approach from a normal continuous level measurement system. Each dispensing tank can use only one low-level sensor. Therefore, the dispensing tank controller cannot directly measure the final full level. Instead, it detects the low-level condition and relies on the supply controller to discharge a known measured volume into the tank."))
    p.append(heading("1.1 Dispensing Tank Level Detection", 2))
    p.append(paragraph("A single low-level sensor is fitted at the minimum acceptable liquid height of each dispensing tank. Suitable technologies include float switches, capacitive liquid level switches, and optical liquid level switches. For hospital chemical dispensing, a non-contact or chemically isolated switch is preferred to reduce contamination and corrosion."))
    p.append(table(["Method", "Suitability", "Comments"], [
        ["Float switch", "Good for simple low-level detection", "Low cost and reliable, but moving parts may wear or stick."],
        ["Capacitive level switch", "Very suitable", "Can detect liquid through some non-metal tank walls and has no moving parts."],
        ["Optical level switch", "Suitable for clean transparent liquid", "Compact but may be affected by deposits, bubbles, or staining."],
    ], [2200, 3000, 4200]))
    p.append(paragraph("Recommended method: a capacitive or sealed float low-level switch for each dispensing tank. The Wokwi simulation uses an ultrasonic sensor to demonstrate level behavior, but the final design should use only a low-level switch to satisfy the project constraint."))
    p.append(heading("1.2 Refilled Level Control by Discharged Volume", 2))
    p.append(paragraph("Because no full-level sensor is available in the dispensing tank, the refill target must be controlled by volume. The required refill volume is calculated from the known tank geometry and the position of the low-level switch. For example, if the low-level switch corresponds to 20 percent tank volume and the target is 80 percent, the refill volume is 60 percent of tank capacity."))
    p.append(paragraph("Actual volume delivered is measured using a flow meter. The supply controller closes the valve or stops the pump when the measured accumulated volume reaches the required setpoint."))
    p.append(heading("1.3 Concentrated Chemical Tank Remaining Level", 2))
    p.append(paragraph("The concentrated chemical tank cannot contain any level sensor. Therefore, remaining chemical is estimated externally or computationally. The recommended method is a computational inventory model using cumulative measured flow from the chemical flow meter."))
    p.append(paragraph("Estimated remaining chemical volume = initial chemical volume - cumulative chemical volume dispensed. The estimate is reset when a new chemical container is installed. Accuracy can be improved by using a load cell under the chemical container, because this measures the container mass externally without inserting a level sensor into the tank."))
    p.append(table(["Method", "Internal tank sensor required?", "Accuracy", "Recommendation"], [
        ["Cumulative flow totalization", "No", "Good if flow meter is calibrated", "Recommended base method."],
        ["External load cell under chemical container", "No", "Very good if vibration is controlled", "Recommended optional verification method."],
        ["Manual operator entry after replacement", "No", "Depends on operator discipline", "Use only as backup."],
    ], [2600, 2300, 2000, 3200]))

    p.append(heading("Chapter 2: Component Selection and Market Product Evaluation", 1))
    p.append(paragraph("The selected components must satisfy the functional constraints, support safe fail-off behavior, and be practical for simulation and real deployment. Prices are approximate USD values from vendor pages available in May 2026 and should be confirmed before purchasing."))
    p.append(heading("2.1 Control Valves", 2))
    p.append(table(["Product", "Approx. cost", "Features", "Decision"], [
        ["Adafruit 12 V plastic solenoid valve", "USD 6.95", "Normally closed, 1/2 inch, suitable for water prototype", "Best low-cost prototype valve."],
        ["Generic 12 V brass solenoid valve", "USD 8-15", "Stronger body and common pipe fittings", "Good for robust water line use."],
        ["Industrial stainless steel 24 V solenoid valve", "USD 25-60", "Industrial duty, better sealing and durability", "Best final installation choice."],
    ], [2600, 1700, 3300, 2600]))
    p.append(paragraph("Final selection: normally closed solenoid valves. They are safer because they automatically close during power failure."))
    p.append(heading("2.2 Flow Meters", 2))
    p.append(table(["Product", "Approx. cost", "Features", "Decision"], [
        ["Adafruit 1/2 inch liquid flow meter", "USD 9.95", "Hall effect pulse output, 1-30 L/min", "Good prototype choice."],
        ["YF-S201 hall effect flow sensor", "USD 3-8", "Low cost, pulse output", "Acceptable for student prototype after calibration."],
        ["Industrial turbine or oval gear flow meter", "USD 30-100", "Better repeatability and chemical compatibility", "Recommended for final dosing accuracy."],
    ], [2600, 1700, 3300, 2600]))
    p.append(paragraph("Final selection: a calibrated flow meter must be used in the chemical line. This is mandatory because PWM pump duty cycle alone cannot guarantee accurate flow rate."))
    p.append(heading("2.3 Variable Rate Chemical Pump", 2))
    p.append(table(["Product", "Approx. cost", "Features", "Decision"], [
        ["Adafruit 12 V peristaltic pump", "USD 24.95", "PWM controllable DC motor, fluid remains inside tube", "Best prototype chemical pump."],
        ["DFRobot peristaltic pump module", "USD 15-25", "Arduino-friendly dosing pump", "Good alternative."],
        ["Industrial chemical dosing peristaltic pump", "USD 80-250", "Chemical compatible tube, long duty cycle, adjustable speed", "Recommended final deployment."],
    ], [2600, 1700, 3300, 2600]))
    p.append(paragraph("Final selection: a peristaltic pump controlled by PWM with flow meter feedback. Peristaltic pumping is preferred because the chemical contacts only the tube."))
    p.append(heading("2.4 Dispensing Tank Low-Level Sensors", 2))
    p.append(table(["Product/type", "Approx. cost", "Features", "Decision"], [
        ["Sealed float switch", "USD 2-10", "Simple low-level switching", "Good for low-cost systems."],
        ["Capacitive non-contact liquid level switch", "USD 5-20", "No moving parts, can detect through tank wall", "Recommended for dispensing tanks."],
        ["Optical liquid level switch", "USD 8-25", "Compact electronic switching", "Useful if chemical staining is not an issue."],
    ], [2600, 1700, 3300, 2600]))
    p.append(heading("2.5 Controllers and Additional Components", 2))
    p.append(table(["Component", "Approx. cost", "Reason for use"], [
        ["ESP32 DevKit / ESP32 Feather", "USD 8-20 / USD 19.95", "WiFi, ADC, PWM, GPIO and Arduino support."],
        ["ESP32 LoRa board", "USD 18-30", "Useful when dispensing tanks are far from WiFi coverage."],
        ["Relay or MOSFET driver module", "USD 2-10", "Required to drive valves and pumps safely."],
        ["I2C LCD", "USD 3-8", "Local status display."],
        ["Warning LED and buzzer", "USD 1-5", "Local fault alarm."],
        ["Flyback diode and fuse", "Low cost", "Electrical protection for inductive loads."],
    ], [2700, 1700, 5200]))

    p.append(heading("Chapter 3: Failure Detection and Fail-Safe Methods", 1))
    p.append(paragraph("Failure detection uses both direct sensor feedback and computational checks. Since the dispensing tank has only a low-level sensor, the most important safety protections are flow-meter totalization, timeout monitoring, and normally closed valves."))
    p.append(table(["Failure", "Detection method", "Fail-safe action"], [
        ["Low-level sensor stuck active", "Same tank repeatedly requests refill immediately after a completed measured refill.", "Disable that tank request, raise maintenance alarm."],
        ["Low-level sensor stuck inactive", "No request for an unusually long usage period; optional manual inspection or usage model detects abnormal condition.", "Raise inspection alert and prevent automatic assumption of full tank."],
        ["Pump running but no chemical flow", "PWM command active but flow meter pulse count remains zero.", "Stop pump, close valves, alarm pump or blockage fault."],
        ["Valve stuck open", "Flow detected after valve command is OFF.", "Cut master shutoff valve and raise high priority alarm."],
        ["Valve stuck closed", "Valve command ON but no flow detected.", "Stop sequence and queue next tank only after fault is acknowledged."],
        ["Chemical inventory estimate below required volume", "Computed remaining volume is less than next refill volume plus safety reserve.", "Do not start refill; alert operator to replace chemical container."],
        ["Communication loss", "MQTT heartbeat or acknowledgement timeout.", "All actuators remain OFF; tank keeps local low-level warning."],
        ["Wrong volume delivered", "Flow total differs from target or exceeds tolerance.", "Stop transfer and log dosing error."],
        ["Power failure", "Controller restart or supply voltage loss.", "Normally closed valves shut; software starts with outputs OFF."],
    ], [2600, 3300, 3900]))
    p.append(paragraph("Key fail-safe principles are: normally closed valves, actuator outputs OFF at boot, watchdog timers, maximum state timeouts, flow based volume cutoff, master shutoff valve, local alarm, and logged events at the central controller."))

    p.append(heading("Chapter 4: Data Collection and Communication Methods", 1))
    p.append(paragraph("Dispensing tanks may be distributed across hospital premises. The system must collect tank requests, queue them, send refill approval, and receive refill status. At least two communication methods were evaluated."))
    p.append(table(["Method", "Advantages", "Disadvantages", "Suitability"], [
        ["WiFi + MQTT", "Low cost with ESP32, easy dashboards, supported by Wokwi.", "Requires WiFi coverage and proper security.", "Recommended for prototype and WiFi-covered areas."],
        ["LoRa / LoRaWAN", "Long range and good for distributed buildings.", "Lower data rate and needs a gateway.", "Recommended for far tanks or poor WiFi zones."],
        ["Zigbee mesh", "Good indoor mesh networking and low power.", "Needs extra modules and gateway.", "Alternative for dense indoor deployments."],
    ], [2300, 2900, 2900, 2600]))
    p.append(paragraph("The implemented simulation uses WiFi and MQTT. In a full hospital deployment, WiFi/MQTT should be used where reliable network coverage exists, while LoRaWAN should be considered for distant tanks."))
    p.append(heading("4.1 Central Queue Control", 2))
    p.append(paragraph("The central controller stores refill requests in a first-request-first-serve queue. It grants refill permission to only the first waiting tank. All other tanks remain in waiting state until the active refill completes or fails."))

    p.append(heading("Chapter 5: Complete System Schematic Block Diagram", 1))
    p.append(paragraph("The following block diagram shows the complete system architecture.", bold=True))
    p.append(paragraph(
        "Dispensing Tank 1 low-level sensor -> Tank Controller 1 -> Communication Network -> Central Queue Controller\n"
        "Dispensing Tank 2 low-level sensor -> Tank Controller 2 -> Communication Network -> Central Queue Controller\n"
        "Dispensing Tank N low-level sensor -> Tank Controller N -> Communication Network -> Central Queue Controller\n\n"
        "Central Queue Controller -> Supply ESP32 Controller\n"
        "Supply ESP32 -> PWM Chemical Pump -> Chemical Flow Meter -> Mixing/Discharge Line -> Selected Dispensing Tank\n"
        "Supply ESP32 -> Water Valve -> Water Flow Meter -> Mixing/Discharge Line -> Selected Dispensing Tank\n"
        "Supply ESP32 -> Warning LED/Buzzer/LCD\n"
        "Chemical Remaining Volume = Initial Volume - Cumulative Measured Chemical Flow",
        font="Consolas",
        size=18,
    ))

    p.append(heading("Chapter 6: Controller and Sensor Schematic Diagram", 1))
    p.append(heading("6.1 Supply Controller Connections", 2))
    p.append(table(["ESP32 pin", "Connected component", "Purpose"], [
        ["GPIO34", "Water level input in simulation", "Represents purified water tank remaining level."],
        ["GPIO35", "Chemical level input in simulation", "Represents computational/external chemical availability in prototype simulation."],
        ["GPIO19", "Water valve driver / LED", "Controls purified water inlet valve."],
        ["GPIO23", "Chemical pump driver / LED", "Controls chemical pump stage."],
        ["GPIO25", "Mixer or transfer valve driver / LED", "Controls mixing/transfer stage."],
        ["GPIO33", "Warning LED", "Visual fault indication."],
        ["GPIO32", "Buzzer", "Audible alarm."],
        ["GPIO21/GPIO22", "I2C LCD", "Local status display."],
    ], [1900, 3300, 4300]))
    p.append(heading("6.2 Dispensing Tank Controller Connections", 2))
    p.append(table(["ESP32 pin", "Connected component", "Purpose"], [
        ["Digital input", "Low-level switch in final design", "Detects level below minimum volume."],
        ["GPIO5/GPIO18", "HC-SR04 in Wokwi simulation", "Simulates tank level only for demonstration."],
        ["GPIO19", "Tank OK LED", "Indicates normal state."],
        ["GPIO23", "Tank Low LED", "Indicates refill request condition."],
        ["GPIO21/GPIO22", "I2C LCD", "Displays refill state and progress."],
    ], [1900, 3300, 4300]))

    p.append(heading("Chapter 7: Operational Algorithms and State Diagrams", 1))
    p.append(heading("7.1 Dispensing Tank Controller Algorithm", 2))
    p.append(paragraph(
        "START -> Connect WiFi/MQTT -> Monitor low-level sensor ->\n"
        "If low-level sensor is inactive: show Tank OK -> continue monitoring\n"
        "If low-level sensor is active: send refill request -> wait for queue approval/status ->\n"
        "Show Waiting / Filling / Completed / Failed -> return to monitoring",
        font="Consolas",
        size=18,
    ))
    p.append(heading("7.2 Central Controller Queue Algorithm", 2))
    p.append(paragraph(
        "START -> Receive refill requests -> Add requests to FCFS queue ->\n"
        "If no refill active: select first tank in queue -> command supply controller ->\n"
        "Wait for complete/fail -> remove completed request -> serve next request",
        font="Consolas",
        size=18,
    ))
    p.append(heading("7.3 Supply Controller Algorithm", 2))
    p.append(paragraph(
        "START -> Connect WiFi/MQTT -> Wait for approved tank refill command ->\n"
        "Check chemical estimated remaining volume -> Check purified water availability ->\n"
        "Start pump/valves -> Count flow meter pulses -> Adjust PWM if required ->\n"
        "Stop when target volume is delivered -> Send REFILL_COMPLETE -> Update chemical inventory estimate",
        font="Consolas",
        size=18,
    ))

    p.append(heading("Chapter 8: Wokwi Simulation and Source Code Attachment", 1))
    p.append(paragraph("The project was implemented using Wokwi and PlatformIO. The simulation uses two ESP32 controllers: one supply controller and one dispensing tank controller. The Wokwi version demonstrates the refill request, water and chemical activation, mixing stage, transfer stage, status messages, tank LEDs, LCD messages, and simulated tank level increase."))
    p.append(table(["File", "Purpose"], [
        ["src/tank_controller.cpp", "Dispensing tank controller program."],
        ["src/supply_controller.cpp", "Supply controller, dosing, mixing, alarm, and MQTT program."],
        ["diagram_tank.json", "Wokwi tank wiring."],
        ["diagram_supply.json", "Wokwi supply wiring."],
        ["platformio.ini", "Build configuration for tank and supply environments."],
    ], [3000, 6500]))
    p.append(paragraph("Important note: the simulation uses an ultrasonic sensor and potentiometers for demonstration because Wokwi does not directly represent every industrial sensor. The final design should use a single low-level sensor per dispensing tank and flow-meter-based discharged volume control."))
    p.append(page_break())

    p.append(heading("Appendix A: Source Code", 1))
    for filename in ["src/tank_controller.cpp", "src/supply_controller.cpp", "platformio.ini"]:
        path = Path(filename)
        if path.exists():
            p.append(code_block(filename, path.read_text(encoding="utf-8", errors="replace")))

    p.append(heading("References", 1))
    refs = [
        "Adafruit. Plastic Water Solenoid Valve - 12 V - 1/2 inch nominal. https://www.adafruit.com/product/997",
        "Adafruit. Liquid Flow Meter - Plastic 1/2 inch NPS threaded. https://www.adafruit.com/product/828",
        "Adafruit. Peristaltic Liquid Pump with Silicone Tubing - 12 V DC. https://www.adafruit.com/product/1150",
        "DFRobot. A02YYUW Waterproof Ultrasonic Sensor for Arduino / ESP32. https://www.dfrobot.com/product-1935.html",
        "DFRobot. Industrial Stainless Steel Submersible Pressure Level Sensor. https://www.dfrobot.com/product-1863.html",
        "Adafruit. HUZZAH32 ESP32 Feather Board. https://www.adafruit.com/product/3405",
        "Adafruit. Feather M0 RFM96 LoRa Radio. https://www.adafruit.com/product/3179",
        "Digi. Digi XBee 3 Zigbee 3 RF Module. https://www.digi.com/products/embedded-systems/digi-xbee/rf-modules/2-4-ghz-rf-modules/xbee3-zigbee-3",
        "Heltec. WiFi LoRa 32 V3 ESP32-S3 + SX1262 board. https://heltec.org/project/wifi-lora-32-v3/",
    ]
    for ref in refs:
        p.append(bullet(ref))
    return "".join(p)


def write_docx():
    body = build_body()
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/document.xml", document_xml(body))
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/numbering.xml", numbering_xml)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    print(OUT.resolve())


if __name__ == "__main__":
    write_docx()
