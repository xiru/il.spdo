/*

 Sistema de Protocolo de Documentos - SPDO, 2015
 
 Este script apaga todos os registros de todas as tabelas do banco spdo
 
 OS REGISTROS APAGADOS NÃO PODERÃO SER RECUPERADOS! USE COM CAUTELA

 Execute este script com o seguinte comando: 

    mysql -uroot -p spdo < clean_spdo.sql 

*/

SET FOREIGN_KEY_CHECKS = 0;

truncate anexo;
truncate anexo_history;
truncate area;
truncate area_history;
truncate fluxo;
truncate fluxo_history;
truncate log;
truncate log_history;
truncate notificacao;
truncate notificacao_history;
truncate observacao;
truncate observacao_history;
truncate pessoa;
truncate pessoa_destino;
truncate pessoa_destino_history;
truncate pessoa_history;
truncate pessoa_origem;
truncate pessoa_origem_history;
truncate protocolo;
truncate protocolo_history;
truncate referencia;
truncate referencia_history;
truncate responsavel;
truncate responsavel_history;
truncate situacao;
truncate situacao_history;
truncate tipodocumento;
truncate tipodocumento_history;
truncate tipoentrega;
truncate tipoentrega_history;
truncate tramite;
truncate tramite_history;
truncate tramite_inbox;
truncate tramite_inbox_history;
truncate tramite_outbox;
truncate tramite_outbox_history;
truncate transicao;
truncate transicao_history;
truncate uf;
truncate uf_history;

SET FOREIGN_KEY_CHECKS = 1;
