/** Export recorded research tables with a white background and black text.
 * Requires @oai/artifact-tool. CSVs remain the public, dependency-light format.
 * Run tools/build_tables.py first. No experimental data are changed here.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const payload = JSON.parse(await fs.readFile(path.join(root,'outputs/workbook_payload.json'),'utf8'));
const qa = path.join(root,'outputs/workbook_qa');
await fs.mkdir(qa,{recursive:true});
await fs.mkdir(path.join(root,'datas/excel'),{recursive:true});
const col = n => {let result='';for(n++;n>0;n=Math.floor((n-1)/26)) result=String.fromCharCode(65+(n-1)%26)+result;return result;};
for (const [group,filename] of [['main','RFOTO_ABC_Main_Results.xlsx'],['supplement','RFOTO_ABC_Supplementary_Statistics.xlsx']]) {
  const wb=Workbook.create();
  for(const item of payload[group]) {
    const sh=wb.worksheets.add(item.sheet);
    const width=item.headers.length;
    const lastRow=item.rows.length+5;
    const area=sh.getRange(`A1:${col(width-1)}${lastRow+1}`);
    area.format={fill:'#FFFFFF',font:{name:'Arial',size:10,color:'#000000'},rowHeight:19,verticalAlignment:'center'};
    sh.showGridLines=false;
    sh.getRange('A1').values=[[item.title]];
    sh.getRange('A1').format.font={name:'Arial',size:14,bold:true,color:'#000000'};
    sh.getRange('A1').format.rowHeight=25;
    sh.getRange('A2').values=[[item.source]];
    // The full statistical notes and upstream mappings also remain in table_index.json.
    sh.getRange('A3').values=[[item.note]];
    sh.getRange('A2:A3').format.font={name:'Arial',size:10,color:'#000000',italic:true};
    sh.getRange(`A5:${col(width-1)}5`).values=[item.headers];
    if(item.rows.length) sh.getRange(`A6:${col(width-1)}${lastRow}`).values=item.rows;
    const header=sh.getRange(`A5:${col(width-1)}5`);
    header.format.font={name:'Arial',size:10,bold:true,color:'#000000'};
    header.format.wrapText=true;
    header.format.rowHeight=44;
    header.format.horizontalAlignment='center';
    header.format.borders={bottom:{style:'thin',color:'#000000'},top:{style:'thin',color:'#000000'}};
    for(let j=0;j<width;j++) {
      const h=item.headers[j];
      const data=sh.getRange(`${col(j)}6:${col(j)}${lastRow}`);
      const values=item.rows.map(r=>r[j]).filter(v=>v!==null);
      const numeric=values.length>0 && values.every(v=>typeof v==='number');
      const longest=Math.max(h.length,...values.slice(0,2040).filter(v=>typeof v==='string').map(v=>v.length));
      sh.getRange(`${col(j)}5:${col(j)}${lastRow}`).format.columnWidth=numeric?Math.min(22,Math.max(14,h.length*.75)):Math.min(80,Math.max(22,longest+3));
      data.format.horizontalAlignment=numeric?'right':'left';
      if(h==='initialization') data.format.horizontalAlignment='center';
      if(numeric){
        const integer=values.every(Number.isInteger);
        data.setNumberFormat(integer?'0': /p_raw|p_holm/.test(h)?'0.000000E+00':/deadline_rate|violation_rate/.test(h)?'0.00%':'0.000000');
      }
    }
    if(item.rows.length>20)sh.freezePanes.freezeRows(5);
    if(width>8)sh.freezePanes.freezeColumns(Math.min(2,width));
  }
  wb.recalculate();
  const audit=[];
  for (const item of payload[group]) {
    const info=await wb.inspect({kind:'table',range:`'${item.sheet}'!A5:F8`,include:'values,formulas',tableMaxRows:4,tableMaxCols:6,maxChars:2000});
    audit.push(info.ndjson);
    for(let start=0;start<item.headers.length;start+=8){
      const end=Math.min(start+7,item.headers.length-1);
      const preview=await wb.render({sheetName:item.sheet,range:`${col(start)}1:${col(end)}${Math.min(item.rows.length+5,15)}`,scale:1,format:'png'});
      await fs.writeFile(path.join(qa,`${group}_${item.sheet}_${start}.png`),new Uint8Array(await preview.arrayBuffer()));
    }
  }
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'final error scan',maxChars:3000});
  audit.push(errors.ndjson);
  await fs.writeFile(path.join(qa,`${group}_inspection.json`),JSON.stringify(audit,null,2));
  const output=await SpreadsheetFile.exportXlsx(wb);
  await output.save(path.join(root,'datas/excel',filename));
  console.log(`Exported ${filename}: ${payload[group].length} sheets; white background, black text.`);
}
