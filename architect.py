/**
 * [Audit Report Generator] - v14.0
 * * UPDATES:
 * - SMART TABS: Organizes backups by date (Newest -> Left).
 * - CLUTTER CONTROL: Hides backups older than the most recent 5.
 * - PLACEMENT: Main Audit Tab is always locked to Position 1 (Far Left).
 * - PRESERVED: Deep Clean, Colors, Text Wrap, Logic, etc.
 */

const SOURCE_SPREADSHEET_ID = '1StoJvRIdQp1xOD2sV1coY5H0XXXAo1GcbayP7zORrCI';

function runAuditReport() {
  console.log("Starting Audit Report generation v14.0...");
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const auditSheet = ss.getSheetByName("Audit Report") || ss.getActiveSheet();
  
  // --- 1. READ CONTROL INPUTS ---
  const tabName = auditSheet.getRange("A1").getValue();
  const currentC1Text = auditSheet.getRange("C1").getValue();
  const controlMode = auditSheet.getRange("E1").getValue();   
  const specificDateInput = auditSheet.getRange("F1").getValue(); 
  
  if (!tabName) { SpreadsheetApp.getUi().alert("Error: Cell A1 (Tab Name) is empty."); return; }
  if (!controlMode) { SpreadsheetApp.getUi().alert("Error: Cell E1 (Date Mode) is empty."); return; }

  // Parse current C1
  const currentContext = parseAuditContext(currentC1Text);
  if (!currentContext) {
    SpreadsheetApp.getUi().alert("Error: C1 is invalid. Needs format like: 'Audit Report for Thursday, January 8th, 2026'");
    return;
  }

  // --- 2. CALCULATE NEW DATE ---
  let newDateObj = new Date(); 
  
  if (controlMode === "Tomorrow") {
    const today = new Date();
    newDateObj = new Date(today);
    newDateObj.setDate(today.getDate() + 1);
  } 
  else if (controlMode === "Following Day") {
    const c1Date = new Date(currentContext.year, currentContext.monthIndex, currentContext.dayInt);
    newDateObj = new Date(c1Date);
    newDateObj.setDate(c1Date.getDate() + 1);
  } 
  else if (controlMode === "Specific Date") {
    if (!specificDateInput) {
      SpreadsheetApp.getUi().alert("Error: 'Specific Date' selected but F1 is empty.");
      return;
    }
    newDateObj = parseSpecificDate(specificDateInput); 
    if (!newDateObj) {
      SpreadsheetApp.getUi().alert("Error: Could not parse F1. Format should be 'MM/DD/YYYY' (e.g., 01/08/2026).");
      return;
    }
  }

  // --- 3. BACKUP CURRENT STATE ---
  createBackup(ss, auditSheet, currentC1Text);

  // >> SMART ORGANIZE TABS (Newest to Left, Hide Old) <<
  organizeTabs(ss);

  // --- 4. UPDATE C1 WITH NEW DATE ---
  const newC1Text = generateC1String(newDateObj);
  auditSheet.getRange("C1").setValue(newC1Text);
  
  const newContext = parseAuditContext(newC1Text);
  console.log(`New Target: ${newContext.dateFull} (${newContext.weekday})`);

  // --- 5. CONNECT & DEEP CLEAN ---
  let sourceSheet;
  try {
    const sourceSS = SpreadsheetApp.openById(SOURCE_SPREADSHEET_ID);
    sourceSheet = sourceSS.getSheetByName(tabName);
    if (!sourceSheet) throw new Error(`Tab "${tabName}" not found.`);
  } catch (e) {
    SpreadsheetApp.getUi().alert(`Connection Error: ${e.message}`);
    return;
  }

  // >> DELETE & INSERT LOGIC <<
  const maxRows = auditSheet.getMaxRows();
  const lastCol = auditSheet.getMaxColumns();

  // 1. Remove Bandings
  const fullRange = auditSheet.getRange(1, 1, maxRows, lastCol);
  fullRange.getBandings().forEach(b => b.remove());

  // 2. Delete Old Rows (From Row 3 to End)
  if (maxRows > 2) {
    auditSheet.deleteRows(3, maxRows - 2);
  }

  // 3. Clear Row 2
  auditSheet.getRange(2, 1, 1, lastCol).clear({contentsOnly: true, formatOnly: true});

  // 4. Insert 100 Fresh Rows
  auditSheet.insertRowsAfter(2, 100);

  // 5. Sanitize New Rows
  const cleanRange = auditSheet.getRange(2, 1, 101, lastCol);
  cleanRange.clear({formatOnly: true});
  cleanRange.setBackground(null);
  cleanRange.breakApart();

  // --- 6. FETCH & PROCESS ---
  const rawData = sourceSheet.getDataRange().getValues();
  const processedData = processSourceData(rawData, newContext);

  // --- 7. WRITE & FORMAT ---
  let currentRow = 2;
  
  // Weekly: #ff9900
  currentRow = writeSection(auditSheet, currentRow, "WEEKLY/DAILY DEALS", processedData.weekly, "#ff9900");
  
  // Monthly: #00ffff
  currentRow = writeSection(auditSheet, currentRow, "MONTHLY DEALS", processedData.monthly, "#00ffff");
  
  // Sale: #ff00ff
  currentRow = writeSection(auditSheet, currentRow, "SALE DEALS", processedData.sale, "#ff00ff");

  console.log("Audit Report completed.");
}

/**
 * >> NEW HELPER: Organizes Tabs (Sorts by Date, Hides Old)
 */
function organizeTabs(ss) {
  const mainSheet = ss.getSheetByName("Audit Report");
  if (!mainSheet) return;

  // 1. Lock Main Sheet to Position 1
  ss.setActiveSheet(mainSheet);
  ss.moveActiveSheet(1);

  // 2. Find and Parse all Backup Sheets
  const allSheets = ss.getSheets();
  const backups = [];

  allSheets.forEach(sheet => {
    const name = sheet.getName();
    // Check if it's a backup tab
    if (name.startsWith("Audit Report - ")) {
      const dateObj = parseDateFromTabName(name);
      if (dateObj) {
        backups.push({ sheet: sheet, date: dateObj });
      }
    }
  });

  // 3. Sort Descending (Newest Date First)
  backups.sort((a, b) => b.date - a.date);

  // 4. Reorder and Hide/Show
  // We place them starting at Position 2 (Main is #1)
  for (let i = 0; i < backups.length; i++) {
    const sheet = backups[i].sheet;
    
    // Move to correct position (i + 2)
    // Note: We act on the sheet reference
    sheet.activate();
    ss.moveActiveSheet(i + 2);
    
    // Visibility Logic (Top 5 visible, rest hidden)
    if (i < 5) {
      sheet.showSheet();
    } else {
      sheet.hideSheet();
    }
  }

  // Return focus to Main Sheet
  mainSheet.activate();
}

/**
 * Helper: Parses date from Tab Name "Audit Report - Thursday, January 8th, 2026"
 */
function parseDateFromTabName(name) {
  // Regex matches: "Audit Report - <Weekday>, <Month> <Day><Suffix>, <Year>"
  const regex = /Audit Report - \w+, (\w+) (\d+)(?:st|nd|rd|th)?, (\d{4})/;
  const match = name.match(regex);
  if (!match) return null;

  const monthStr = match[1];
  const day = parseInt(match[2], 10);
  const year = parseInt(match[3], 10);

  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const monthIndex = months.findIndex(m => m.toLowerCase() === monthStr.toLowerCase());

  if (monthIndex === -1) return null;
  return new Date(year, monthIndex, day);
}

// --- STANDARD HELPERS BELOW ---

function cleanMisId(rawId) {
  if (!rawId) return "";
  const str = String(rawId);
  return str.replace(/[A-Z0-9]+:\s*/gi, '').trim();
}

function generateC1String(date) {
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const weekday = days[date.getDay()];
  const month = months[date.getMonth()];
  const day = date.getDate();
  const year = date.getFullYear();
  const suffix = (day) => {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) { case 1: return "st"; case 2: return "nd"; case 3: return "rd"; default: return "th"; }
  };
  return `Audit Report for ${weekday}, ${month} ${day}${suffix(day)}, ${year}`;
}

function parseSpecificDate(input) {
  if (Object.prototype.toString.call(input) === '[object Date]') return input;
  const parts = String(input).split('/');
  if (parts.length === 3) {
    const month = parseInt(parts[0], 10) - 1;
    const day = parseInt(parts[1], 10);
    const year = parseInt(parts[2], 10);
    if (!isNaN(month) && !isNaN(day) && !isNaN(year)) return new Date(year, month, day);
  }
  return null;
}

function createBackup(ss, sheet, contextString) {
  const backupName = contextString.replace("Audit Report for", "Audit Report -").trim();
  const existingSheet = ss.getSheetByName(backupName);
  if (existingSheet) ss.deleteSheet(existingSheet);
  const backup = sheet.copyTo(ss);
  backup.setName(backupName);
  // Placement is handled by organizeTabs immediately after this
}

function parseAuditContext(text) {
  if (!text) return null;
  const regex = /Audit Report for (\w+), (\w+) (\d+)(?:st|nd|rd|th)?, (\d{4})/i;
  const match = text.match(regex);
  if (!match) return null;
  const monthStr = match[2];
  const day = parseInt(match[3], 10);
  const year = parseInt(match[4], 10);
  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const monthIndex = months.findIndex(m => m.toLowerCase() === monthStr.toLowerCase());
  if (monthIndex === -1) return null;
  const dateObj = new Date(year, monthIndex, day);
  const mm = ('0' + (dateObj.getMonth() + 1)).slice(-2);
  const dd = ('0' + dateObj.getDate()).slice(-2);
  const yyyy = dateObj.getFullYear();
  const yy = yyyy.toString().slice(-2);
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const calculatedWeekday = days[dateObj.getDay()];
  const dateDisplay = `${mm}/${dd} - ${calculatedWeekday}`; 
  return { 
    weekday: calculatedWeekday.toUpperCase(),
    dayInt: day,
    monthIndex: monthIndex,
    year: year,
    dateDisplay,
    dateShort: `${mm}/${dd}/${yy}`,
    dateLoose: `${dateObj.getMonth() + 1}/${dateObj.getDate()}/${yy}`,
    dateFull: `${mm}/${dd}/${yyyy}`
  };
}

function processSourceData(data, context) {
  const output = { weekly: [], monthly: [], sale: [] };
  let currentSection = 'WEEKLY'; 
  const COLS = { WEEKDAY: 0, SALE_DATE: 2, BRAND: 4, DEAL_INFO: 5, CONTRIB: 7, MONTH_DAY: 10, MIS_ID: 27 };
  const WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const firstCell = String(row[0]).trim();
    if (firstCell === "MONTHLYSTART") { currentSection = 'MONTHLY'; continue; }
    if (firstCell === "SALESTART") { currentSection = 'SALE'; continue; }

    const brand = row[COLS.BRAND];
    if (!brand || String(brand).trim() === "") continue; 

    const deal = row[COLS.DEAL_INFO];
    const contrib = row[COLS.CONTRIB];
    const misId = cleanMisId(row[COLS.MIS_ID]);

    if (currentSection === 'WEEKLY') {
      const rowWeekday = String(row[COLS.WEEKDAY]).toUpperCase();
      if (WEEKDAYS.includes(rowWeekday) && rowWeekday === context.weekday) {
        output.weekly.push([ context.dateDisplay, brand, deal, contrib, misId, "", "" ]);
      }
    } 
    else if (currentSection === 'MONTHLY') {
      if (firstCell === "MONTHLY DEAL") {
        const dateCell = String(row[COLS.MONTH_DAY]);
        let isMatch = false;
        if (dateCell.includes(context.dateShort) || dateCell.includes(context.dateLoose)) { isMatch = true; } 
        else {
          const ordinalMatches = dateCell.match(/(\d+)(?:st|nd|rd|th)/g);
          if (ordinalMatches) {
            const days = ordinalMatches.map(s => parseInt(s));
            if (days.includes(context.dayInt)) isMatch = true;
          }
        }
        if (isMatch) output.monthly.push([ context.dateDisplay, brand, deal, contrib, misId, "", "" ]);
      }
    } 
    else if (currentSection === 'SALE') {
      if (firstCell === "SALE DEAL") {
        const saleDateCell = String(row[COLS.SALE_DATE]);
        if (saleDateCell.includes(context.dateShort) || saleDateCell.includes(context.dateLoose)) {
          output.sale.push([ context.dateDisplay, brand, deal, contrib, misId, "", "" ]);
        }
      }
    }
  }
  return output;
}

function writeSection(sheet, startRow, sectionTitle, dataRows, headerColor) {
  const titleRowIndex = startRow;
  const titleRange = sheet.getRange(titleRowIndex, 1, 1, 7);
  
  titleRange.merge()
    .setValue(sectionTitle)
    .setFontWeight("bold")
    .setFontSize(14)
    .setBackground(headerColor)
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle")
    .setBorder(true, true, true, true, true, true, "black", SpreadsheetApp.BorderStyle.SOLID);

  const headerRowIndex = startRow + 1;
  const headers = ["Date", "Partner", "Deal", "Brand Contribution", "MIS Logic", "Blaze Logic", "Jane Logic"];
  sheet.getRange(headerRowIndex, 1, 1, 7).setValues([headers]); 

  const dataStartRow = startRow + 2;
  let rowsToWrite = 0;
  if (dataRows.length > 0) {
    rowsToWrite = dataRows.length;
    sheet.getRange(dataStartRow, 1, rowsToWrite, 7).setValues(dataRows);
  }

  const totalBodyRows = 1 + (rowsToWrite > 0 ? rowsToWrite : 0);
  const bodyRange = sheet.getRange(headerRowIndex, 1, totalBodyRows, 7);
  
  bodyRange.setBorder(true, true, true, true, true, true, "black", SpreadsheetApp.BorderStyle.SOLID);
  bodyRange.setVerticalAlignment("middle");
  sheet.getRange(headerRowIndex, 1, 1, 7).setFontWeight("bold").setHorizontalAlignment("center");

  if (rowsToWrite > 0) {
    sheet.getRange(dataStartRow, 3, rowsToWrite, 1).setHorizontalAlignment("center");
    sheet.getRange(dataStartRow, 4, rowsToWrite, 1).setHorizontalAlignment("center");
    sheet.getRange(dataStartRow, 5, rowsToWrite, 1).setHorizontalAlignment("center");
    sheet.getRange(dataStartRow, 4, rowsToWrite, 1).setNumberFormat("0%");
  }

  sheet.getRange(headerRowIndex, 3, totalBodyRows, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);

  if (rowsToWrite >= 0) { 
    bodyRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false); 
  }

  return startRow + 2 + (rowsToWrite > 0 ? rowsToWrite : 0) + 1;
}
