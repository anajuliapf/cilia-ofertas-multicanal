/**
 * Aplicação com Apps Script — traz uma tabela (pergunta salva) do Metabase
 * para uma aba do Google Sheets.
 *
 * Configuração (Projeto > Configurações do projeto > Propriedades do script):
 *   METABASE_URL       ex.: https://metabase.suaempresa.com
 *   METABASE_USER      usuário do Metabase
 *   METABASE_PASSWORD  senha do Metabase
 *   QUERY_ID           id da pergunta (card) no Metabase
 *   SPREADSHEET_ID     id da planilha de destino
 *
 * Dica: crie um acionador (trigger) baseado em tempo para rodar
 * AtualizarTabela() automaticamente.
 */
function AtualizarTabela() {
  var props = PropertiesService.getScriptProperties();
  var metabaseurl = props.getProperty('METABASE_URL');
  var queryid = props.getProperty('QUERY_ID');
  var metabaseuser = props.getProperty('METABASE_USER');
  var metabasepassword = props.getProperty('METABASE_PASSWORD');
  var spreadsheetid = props.getProperty('SPREADSHEET_ID');
  var sheetname = 'Ofertas';

  // 1. Login no Metabase para obter o token de sessão
  var responseloginmetabase = UrlFetchApp.fetch(metabaseurl + '/api/session', {
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    payload: JSON.stringify({ username: metabaseuser, password: metabasepassword })
  });
  var sessiontoken = JSON.parse(responseloginmetabase.getContentText()).id;

  // 2. Executa a pergunta salva e recebe o resultado em JSON
  var responsemetabase = UrlFetchApp.fetch(metabaseurl + '/api/card/' + queryid + '/query/json', {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Metabase-Session': sessiontoken
    }
  });
  var responsebody = JSON.parse(responsemetabase.getContentText());

  // 3. Limpa a aba e grava os dados com as colunas na ordem definida
  var sheet = SpreadsheetApp.openById(spreadsheetid).getSheetByName(sheetname);
  sheet.clear();

  if (responsebody.length > 0) {
    // Defina aqui as colunas na ordem desejada
    var orderedColumns = ['id', 'account_id', 'account_name', 'document_identifier'];
    var values = [orderedColumns].concat(
      responsebody.map(function (obj) {
        return orderedColumns.map(function (key) { return obj[key]; });
      })
    );
    // Alternativa: usar todas as colunas na ordem retornada pelo Metabase
    // var headerrow = Object.keys(responsebody[0]);
    // var values = [headerrow].concat(responsebody.map(obj => headerrow.map(key => obj[key])));

    sheet.getRange(1, 1, values.length, values[0].length).setValues(values);
    Logger.log('Resultados da query do Metabase adicionados à planilha');
  } else {
    Logger.log('A query do Metabase não retornou resultado');
  }

  // 4. Registra a data/hora da última atualização
  var timestamp = new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
  sheet.getRange('M1').setValue('Última atualização: ' + timestamp);
}
