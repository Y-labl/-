<!--
1.若hbase测试成功，所有配置（三种文档）的文档内容表均设置为hbase存储类型
2.若hbase测试失败，且任意一种文档数据库类型配置属于bigDataType（大数据场景数据库类型）且测试成功时，
  三种文档内容表均设置为hbase存储方案（同时hbase测试必须成功）；反之三种文档内容表不采用hbase方案
-->
<template>
  <div class="h-fit" style="overflow-y:scroll;">
    <div class="app-container"
         v-loading.fullscreen.lock="containerLoading"
         :element-loading-text="$t('正在加载文档存储配置，请稍候！')"
         element-loading-spinner="hos-icon-loading"
         element-loading-background="rgba(0, 0, 0, 0.8)">
      <!-- HTML文档-->
      <hos-container>
        <hos-header class="config-header-title" style="border-top: 0px">
          {{$t('HTML文档')}}
          <hos-tooltip class="item" effect="dark" :content="$t('HTML文档存储相关配置信息')" placement="right">
            <i class="hos-icon-info"></i>
          </hos-tooltip>
          <hos-button style="float: right;margin: 5px auto;" @click="handleSaveDataSource(0)" type="primary">{{$t('保存HTML文档数据源')}}</hos-button>
        </hos-header>
        <hos-main style="">
          <hos-form   :model="configInfoForm" label-width="auto">
            <hos-form-item :label="configInfoForm.HTMLDBCODEITEMNAME">
              <hos-select
                  :placeholder="$t('请选择数据源')"
                  v-model="configInfoForm.HTMLDBCODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.HTMLDBCODE,'0','HTMLDBCODE')">
                <hos-option
                    v-for="item in dbConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.dbType+') '+item.serverIp+':'+item.serverPort+'/'+item.dbName+''"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.HTMLDBCODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('HTML_DB_CODE')"
                  :loading="testButtonLoading.HTMLDBCODE"
                  size="mini" class="test-button"
                  @click="testDataSource('HTML_DB_CODE')">
                {{$t('测试')}}
                <i v-show="!testButtonLoading.HTMLDBCODE&&testStatus.HTMLDBCODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HTMLDBCODE&&testStatus.HTMLDBCODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('隶属系统')">
              <hos-select
                  :placeholder="$t('请选择隶属系统')"
                  v-model="configInfoForm.HTMLORGSYSTEM"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.HTMLORGSYSTEM,'0','HTMLORGSYSTEM')">
                <hos-option
                    v-for="item in forOrganName"
                    :key="item.id"
                    :label="item.access_name"
                    :value="item.id">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{affiliatedSystem}}</label>
              <hos-button
                  v-if="false"
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button"
                  @click="testConnection('HBASE_CODE','html')">
                测试
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('文档内容存储')" @input="changeUseHBase('0')">
              <hos-radio v-model="configInfoForm.HTMLUSEHBASE" label="0" >{{$t('使用文档索引库对文档内容进行存储')}}</hos-radio>
              <hos-radio v-model="configInfoForm.HTMLUSEHBASE" label="1">{{$t('使用Hbase数据库对文档内容进行存储')}}</hos-radio>
            </hos-form-item>
            <!--          </hos-container>-->
            <hos-form-item v-if="configInfoForm.HTMLUSEHBASE == 1" :label="configInfoForm.HBASECODEITEMNAME">
              <hos-select
                  placeholder="请选择数据源"
                  v-model="configInfoForm.HBASECODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.HBASECODE,'1','HBASECODE')">
                <hos-option
                    v-for="item in HbaseConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.bigdataType+') '"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.HBASECODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button"
                  @click="testConnection('HBASE_CODE')">
                测试
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="configInfoForm.HTMLDBTABLEINDEXITEMNAME">
              <hos-tooltip :content="configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLEINDEX"
                           placement="bottom">
                <hos-input v-model="configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLEINDEX"
                           class="default-input-inner":disabled="true"></hos-input>
              </hos-tooltip>
              <hos-tooltip :content="configInfoForm.HTMLDBTABLEINDEXREMARK"
                           placement="bottom">
                <label style="margin-left:10px">{{configInfoForm.HTMLDBTABLEINDEXREMARK}}</label>
              </hos-tooltip>
              <hos-button
                  :type="tableButtonStyle('HTML_DB_TABLE_INDEX')"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.HTMLDBTABLEINDEX"
                  @click="createTable('HTML_DB_CODE','HTML_DB_SCHEMA','HTML_DB_TABLE_INDEX')">
                {{$t('建表')}}
                <i v-show="!tableButtonLoading.HTMLDBTABLEINDEX&&createTableStatus.HTMLDBTABLEINDEX=='1'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="!tableButtonLoading.HTMLDBTABLEINDEX&&createTableStatus.HTMLDBTABLEINDEX=='-1'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>

            <hos-form-item
                :label="configVersion.htmlVersion==0&&testStatus.HBASECODE!='1'||configInfoForm.HTMLUSEHBASE!='1'?configInfoForm.HTMLDBTABLECONTENTITEMNAME:
            configInfoForm.HTMLHBASETABLECONTENTITEMNAME"
            >
              <hos-tooltip
                  :content="configVersion.htmlVersion==0&&testStatus.HBASECODE!='1'||configInfoForm.HTMLUSEHBASE!='1'?configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLECONTENT:
              configInfoForm.HTMLHBASENAMESPACE+'.'+configInfoForm.HTMLHBASETABLECONTENT"
                  placement="bottom"
              >
                <hos-input
                    v-model="configVersion.htmlVersion==0&&testStatus.HBASECODE!='1'||configInfoForm.HTMLUSEHBASE!='1'?configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLECONTENT:
              configInfoForm.HTMLHBASENAMESPACE+'.'+configInfoForm.HTMLHBASETABLECONTENT"
                    :disabled="true"
                    class="default-input-inner"
                >
                </hos-input>
              </hos-tooltip>
              <hos-tooltip
                  :content="configVersion.htmlVersion==0&&testStatus.HBASECODE!='1'||configInfoForm.HTMLUSEHBASE!='1'?configInfoForm.HTMLDBTABLECONTENTREMARK:
            configInfoForm.HTMLHBASETABLECONTENTREMARK"
                  placement="bottom"
              >
                <label style="margin-left:10px">{{configVersion.htmlVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.HTMLDBTABLECONTENTREMARK:
                    configInfoForm.HTMLHBASETABLECONTENTREMARK}}</label>
              </hos-tooltip>
              <!--两种建表情况:hbase和普通数据库，参数通过||分割-->
              <hos-button
                  :type="contentTableStatusShow('HTMLDBTABLECONTENT','HTMLHBASETABLECONTENT', 'HTMLUSEHBASE')=='success'?'primary':'danger'"
                  size="mini"
                  class="test-button"
                  :loading="tableButtonLoading.HTMLDBTABLECONTENT||tableButtonLoading.HTMLHBASETABLECONTENT"
                  @click="createTable('HTML_DB_CODE||HBASE_CODE','HTML_DB_SCHEMA||HTML_HBASE_NAMESPACE',
                       'HTML_DB_TABLE_CONTENT||HTML_HBASE_TABLE_CONTENT', 'HTMLUSEHBASE')">
                {{$t('建表')}}
                <i v-show="contentTableStatusShow('HTMLDBTABLECONTENT','HTMLHBASETABLECONTENT', 'HTMLUSEHBASE')=='success'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="contentTableStatusShow('HTMLDBTABLECONTENT','HTMLHBASETABLECONTENT', 'HTMLUSEHBASE')=='error'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>

            <hos-form-item
                :label="configInfoForm.HTMLDBTABLEDICITEMNAME"
            >
              <hos-tooltip
                  :content="configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLEDIC"
                  placement="bottom"
              >
                <hos-input
                    v-model="configInfoForm.HTMLDBSCHEMA+'.'+configInfoForm.HTMLDBTABLEDIC"
                    :disabled="true"
                    class="default-input-inner"
                >
                </hos-input>
              </hos-tooltip>
              <hos-tooltip
                  :content="configInfoForm.HTMLDBTABLEDICITEMNAME"
                  placement="bottom"
              >
                <label style="margin-left:10px">{{configInfoForm.HTMLDBTABLEDICREMARK}}</label>
              </hos-tooltip>
              <hos-button
                  :type="tableButtonStyle('HTML_DB_TABLE_DIC')"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.HTMLDBTABLEDIC"
                  @click="createTable('HTML_DB_CODE','HTML_DB_SCHEMA','HTML_DB_TABLE_DIC')">
                {{$t('建表')}}
                <i v-show="!tableButtonLoading.HTMLDBTABLEDIC&&createTableStatus.HTMLDBTABLEDIC=='1'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="!tableButtonLoading.HTMLDBTABLEDIC&&createTableStatus.HTMLDBTABLEDIC=='-1'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
          </hos-form>
        </hos-main>
      </hos-container>
      <!--fhir文档-->
      <hos-container>
        <hos-header class="config-header-title">
          {{$t('临床文档')}}
          <hos-tooltip class="item" effect="dark" :content="$t('临床文档存储相关配置信息')" placement="right">
            <i class="hos-icon-info"></i>
          </hos-tooltip>
          <hos-button style="float: right;margin: 5px auto;" @click="handleSaveDataSource(1)" type="primary">{{$t('保存临床文档数据源')}}</hos-button>
        </hos-header>
        <hos-main style="">
          <hos-form   :model="configInfoForm" label-width="auto">
            <hos-form-item :label="configInfoForm.FHIRDBCODEITEMNAME">
              <hos-select
                  :placeholder="$t('请选择数据源')"
                  v-model="configInfoForm.FHIRDBCODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.FHIRDBCODE,'1','FHIRDBCODE')">
                <hos-option
                    v-for="item in dbConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.dbType+') '+item.serverIp+':'+item.serverPort+'/'+item.dbName+''"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.FHIRDBCODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('FHIR_DB_CODE')"
                  :loading="testButtonLoading.FHIRDBCODE"
                  size="mini" class="test-button"
                  @click="testDataSource('FHIR_DB_CODE')">
                {{$t('测试')}}
                <i v-show="!testButtonLoading.FHIRDBCODE&&testStatus.FHIRDBCODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.FHIRDBCODE&&testStatus.FHIRDBCODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('隶属系统')">
              <hos-select
                  :placeholder="$t('请选择隶属系统')"
                  v-model="configInfoForm.FHIRORGSYSTEM"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.FHIRORGSYSTEM,'1','FHIRORGSYSTEM')">
                <hos-option
                    v-for="item in forOrganName"
                    :key="item.id"
                    :label="item.access_name"
                    :value="item.id">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{affiliatedSystem}}</label>
              <hos-button
                  v-if="false"
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button">
                测试
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('文档内容存储')" @input="changeUseHBase('1')">
              <hos-radio v-model="configInfoForm.FHIRUSEHBASE" label="0" >{{$t('使用文档索引库对文档内容进行存储')}}</hos-radio>
              <hos-radio v-model="configInfoForm.FHIRUSEHBASE" label="1">{{$t('使用Hbase数据库对文档内容进行存储')}}</hos-radio>
            </hos-form-item>
            <hos-form-item v-if="configInfoForm.FHIRUSEHBASE == 1" :label="configInfoForm.HBASECODEITEMNAME">
              <hos-select
                  :placeholder="$t('请选择数据源')"
                  v-model="configInfoForm.HBASECODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.HBASECODE,'1','HBASECODE')">
                <hos-option
                    v-for="item in HbaseConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.bigdataType+') '"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.HBASECODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button"
                  @click="testConnection('HBASE_CODE','fhir')">
                {{$t('测试')}}
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="configInfoForm.FHIRDBTABLEINDEXITEMNAME">
              <hos-tooltip :content="configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLEINDEX"
                           placement="bottom">
                <hos-input v-model="configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLEINDEX"
                           class="default-input-inner":disabled="true"></hos-input>
              </hos-tooltip>
              <hos-tooltip :content="configInfoForm.FHIRDBTABLEINDEXREMARK"
                           placement="bottom">
                <label style="margin-left:10px">{{configInfoForm.FHIRDBTABLEINDEXREMARK}}</label>
              </hos-tooltip>
              <hos-button
                  :type="tableButtonStyle('FHIR_DB_TABLE_INDEX')"
                  size="mini"
                  class="test-button" :loading="tableButtonLoading.FHIRDBTABLEINDEX"
                  @click="createTable('FHIR_DB_CODE','FHIR_DB_SCHEMA','FHIR_DB_TABLE_INDEX')">
                {{$t('建表')}}
                <i v-show="!tableButtonLoading.FHIRDBTABLEINDEX&&createTableStatus.FHIRDBTABLEINDEX=='1'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="!tableButtonLoading.FHIRDBTABLEINDEX&&createTableStatus.FHIRDBTABLEINDEX=='-1'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>

            <hos-form-item
                :label="configVersion.fhirVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.FHIRDBTABLECONTENTITEMNAME:
            configInfoForm.FHIRHBASETABLECONTENTITEMNAME"
            >
              <hos-tooltip
                  :content="configVersion.fhirVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLECONTENT:
              configInfoForm.FHIRHBASENAMESPACE+'.'+configInfoForm.FHIRHBASETABLECONTENT"
                  placement="bottom"
              >
                <hos-input
                    v-model="configVersion.fhirVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLECONTENT:
              configInfoForm.FHIRHBASENAMESPACE+'.'+configInfoForm.FHIRHBASETABLECONTENT"
                    :disabled="true"
                    class="default-input-inner"
                >
                </hos-input>
              </hos-tooltip>
              <hos-tooltip
                  :content="configVersion.fhirVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.FHIRDBTABLECONTENTREMARK:
            configInfoForm.FHIRHBASETABLECONTENTREMARK"
                  placement="bottom"
              >
                <label style="margin-left:10px">{{configVersion.fhirVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.FHIRDBTABLECONTENTREMARK:
                    configInfoForm.FHIRHBASETABLECONTENTREMARK}}</label>
              </hos-tooltip>
              <!--两种建表情况:hbase和普通数据库，参数通过||分割-->
              <hos-button
                  :type="contentTableStatusShow('FHIRDBTABLECONTENT','FHIRHBASETABLECONTENT', 'FHIRUSEHBASE')=='success'?'primary':'danger'"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.FHIRDBTABLECONTENT||tableButtonLoading.FHIRHBASETABLECONTENT"
                  @click="createTable('FHIR_DB_CODE||HBASE_CODE','FHIR_DB_SCHEMA||FHIR_HBASE_NAMESPACE',
                       'FHIR_DB_TABLE_CONTENT||FHIR_HBASE_TABLE_CONTENT', 'FHIRUSEHBASE')">
                {{$t('建表')}}
                <i v-show="contentTableStatusShow('FHIRDBTABLECONTENT','FHIRHBASETABLECONTENT', 'FHIRUSEHBASE')=='success'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="contentTableStatusShow('FHIRDBTABLECONTENT','FHIRHBASETABLECONTENT', 'FHIRUSEHBASE')=='error'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item
                :label="configInfoForm.FHIRDBTABLEDICITEMNAME"
            >
              <hos-tooltip
                  :content="configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLEDIC"
                  placement="bottom"
              >
                <hos-input
                    v-model="configInfoForm.FHIRDBSCHEMA+'.'+configInfoForm.FHIRDBTABLEDIC"
                    :disabled="true"
                    class="default-input-inner"
                >
                </hos-input>
              </hos-tooltip>
              <hos-tooltip
                  :content="configInfoForm.FHIRDBTABLEDICITEMNAME"
                  placement="bottom"
              >
                <label style="margin-left:10px">{{configInfoForm.FHIRDBTABLEDICREMARK}}</label>
              </hos-tooltip>
              <hos-button
                  :type="tableButtonStyle('FHIR_DB_TABLE_DIC')"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.FHIRDBTABLEDIC"
                  @click="createTable('FHIR_DB_CODE','FHIR_DB_SCHEMA','FHIR_DB_TABLE_DIC')">
                {{$t('建表')}}
                <i v-show="!tableButtonLoading.FHIRDBTABLEDIC&&createTableStatus.FHIRDBTABLEDIC=='1'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="!tableButtonLoading.FHIRDBTABLEDIC&&createTableStatus.FHIRDBTABLEDIC=='-1'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
          </hos-form>
        </hos-main>
      </hos-container>
      <!--共享文档-->
      <hos-container>
        <hos-header class="config-header-title">
          {{$t('共享文档')}}
          <hos-tooltip class="item" effect="dark" :content="$t('共享文档存储相关配置信息')" placement="right">
            <i class="hos-icon-info"></i>
          </hos-tooltip>
          <hos-button style="float: right;margin: 5px auto;" @click="handleSaveDataSource(2)" type="primary">{{$t('保存共享文档数据源')}}</hos-button>
        </hos-header>
        <hos-main style="">
          <hos-form   :model="configInfoForm" label-width="auto">
            <hos-form-item :label="configInfoForm.CDADBCODEITEMNAME">
              <hos-select
                  :placeholder="$t('请选择数据源')"
                  v-model="configInfoForm.CDADBCODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.CDADBCODE,'2','CDADBCODE')">
                <hos-option
                    v-for="item in dbConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.dbType+') '+item.serverIp+':'+item.serverPort+'/'+item.dbName+''"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.CDADBCODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('CDA_DB_CODE')"
                  :loading="testButtonLoading.CDADBCODE"
                  size="mini" class="test-button"
                  @click="testDataSource('CDA_DB_CODE')">
                {{$t('测试')}}
                <i v-show="!testButtonLoading.CDADBCODE&&testStatus.CDADBCODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.CDADBCODE&&testStatus.CDADBCODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('隶属系统')">
              <hos-select
                  :placeholder="$t('请选择隶属系统')"
                  v-model="configInfoForm.CDAORGSYSTEM"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.CDAORGSYSTEM,'2','CDAORGSYSTEM')">
                <hos-option
                    v-for="item in forOrganName"
                    :key="item.id"
                    :label="item.access_name"
                    :value="item.id">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{affiliatedSystem}}</label>
              <hos-button
                  v-if="false"
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button"
              >
                测试
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="$t('文档内容存储')" @input="changeUseHBase('2')">
              <hos-radio v-model="configInfoForm.CDAUSEHBASE" label="0">{{$t('使用文档索引库对文档内容进行存储')}}</hos-radio>
              <hos-radio v-model="configInfoForm.CDAUSEHBASE" label="1">{{$t('使用Hbase数据库对文档内容进行存储')}}</hos-radio>
            </hos-form-item>

            <hos-form-item v-if="configInfoForm.CDAUSEHBASE == 1" :label="configInfoForm.HBASECODEITEMNAME">
              <hos-select
                  :placeholder="$t('请选择数据源')"
                  v-model="configInfoForm.HBASECODE"
                  filterable
                  loading-text
                  no-data-text
                  no-match-text
                  class="dataSource-select-inner" @change="changeConfigVersionAndStatus(configInfoForm.HBASECODE,'2','HBASECODE')">
                <hos-option
                    v-for="item in HbaseConnectionList"
                    :key="item.databaseConnectionId"
                    :label="item.name+' -- ('+item.bigdataType+') '"
                    :value="item.databaseConnectionId+''">
                </hos-option>
              </hos-select>
              <label style="margin-left:10px;color: grey;">{{configInfoForm.HBASECODEREMARK}}</label>
              <hos-button
                  :type="testButtonStyle('HBASE_CODE')"
                  :loading="testButtonLoading.HBASECODE"
                  size="mini" class="test-button"
                  @click="testConnection('HBASE_CODE','cda')">
                {{$t('测试')}}
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='1'"  class="header-icon hos-icon-success"></i>
                <i v-show="!testButtonLoading.HBASECODE&&testStatus.HBASECODE=='-1'"  class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item :label="configInfoForm.CDADBTABLEINDEXITEMNAME">
              <hos-tooltip :content="configInfoForm.CDADBSCHEMA+'.'+configInfoForm.CDADBTABLEINDEX"
                           placement="bottom">
                <hos-input v-model="configInfoForm.CDADBSCHEMA+'.'+configInfoForm.CDADBTABLEINDEX"
                           class="default-input-inner":disabled="true"></hos-input>
              </hos-tooltip>
              <hos-tooltip :content="configInfoForm.CDADBTABLEINDEXREMARK"
                           placement="bottom">
                <label style="margin-left:10px">{{configInfoForm.CDADBTABLEINDEXREMARK}}</label>
              </hos-tooltip>
              <hos-button
                  :type="tableButtonStyle('CDA_DB_TABLE_INDEX')"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.CDADBTABLEINDEX"
                  @click="createTable('CDA_DB_CODE','CDA_DB_SCHEMA','CDA_DB_TABLE_INDEX')">
                {{$t('建表')}}
                <i v-show="!tableButtonLoading.CDADBTABLEINDEX&&createTableStatus.CDADBTABLEINDEX=='1'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="!tableButtonLoading.CDADBTABLEINDEX&&createTableStatus.CDADBTABLEINDEX=='-1'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
            <hos-form-item
                :label="configVersion.cdaVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.CDADBTABLECONTENTITEMNAME:
            configInfoForm.CDAHBASETABLECONTENTITEMNAME"
            >
              <hos-tooltip
                  :content="configVersion.cdaVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.CDADBSCHEMA+'.'+configInfoForm.CDADBTABLECONTENT:
              configInfoForm.CDAHBASENAMESPACE+'.'+configInfoForm.CDAHBASETABLECONTENT"
                  placement="bottom"
              >
                <hos-input
                    v-model="configVersion.cdaVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.CDADBSCHEMA+'.'+configInfoForm.CDADBTABLECONTENT:
              configInfoForm.CDAHBASENAMESPACE+'.'+configInfoForm.CDAHBASETABLECONTENT"
                    :disabled="true"
                    class="default-input-inner"
                >
                </hos-input>
              </hos-tooltip>
              <hos-tooltip
                  :content="configVersion.cdaVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.CDADBTABLECONTENTREMARK:
            configInfoForm.CDAHBASETABLECONTENTREMARK"
                  placement="bottom"
              >
                <label style="margin-left:10px">{{configVersion.cdaVersion==0&&testStatus.HBASECODE!='1'?configInfoForm.CDADBTABLECONTENTREMARK:
                    configInfoForm.CDAHBASETABLECONTENTREMARK}}</label>
              </hos-tooltip>
              <!--两种建表情况:hbase和普通数据库，参数通过||分割-->
              <hos-button
                  :type="contentTableStatusShow('CDADBTABLECONTENT','CDAHBASETABLECONTENT','CDAUSEHBASE')=='success'?'primary':'danger'"
                  size="mini" class="test-button"
                  :loading="tableButtonLoading.CDADBTABLECONTENT||tableButtonLoading.CDAHBASETABLECONTENT"
                  @click="createTable('CDA_DB_CODE||HBASE_CODE','CDA_DB_SCHEMA||CDA_HBASE_NAMESPACE',
                       'CDA_DB_TABLE_CONTENT||CDA_HBASE_TABLE_CONTENT','CDAUSEHBASE')">
                {{$t('建表')}}
                <i v-show="contentTableStatusShow('CDADBTABLECONTENT','CDAHBASETABLECONTENT', 'CDAUSEHBASE')=='success'"
                   class="header-icon hos-icon-success"></i>
                <i v-show="contentTableStatusShow('CDADBTABLECONTENT','CDAHBASETABLECONTENT', 'CDAUSEHBASE')=='error'"
                   class="header-icon hos-icon-error"></i>
              </hos-button>
            </hos-form-item>
          </hos-form>
        </hos-main>
      </hos-container>

    </div>
  </div>
</template>

<script>
import myFileUpload from "@/components/FileUpload"
const bigDataType=["LIBRA","KUNDB"]
export default {
  name: "CollectConfig",
  components: {
    myFileUpload
  },
  data() {
    return {
      containerLoading: false,
      configInfoForm:{
        HTMLDBTABLEINDEX:"",
        HTMLDBTABLEDIC:"",
        HTMLDBSCHEMA:"",
        HTMLDBCODE:"",
        HTMLUSEHBASE: '0',
        FHIRDBTABLEINDEX:"",
        FHIRDBTABLEDIC:"",
        FHIRDBSCHEMA:"",
        FHIRDBCODE:"",
        FHIRUSEHBASE: '0',
        CDADBCODE:"",
        CDADBSCHEMA:"",
        CDADBTABLEINDEX:"",
        CDAUSEHBASE: '0',
        HTMLDBTABLECONTENT:"",
        FHIRDBTABLECONTENT:"",
        CDADBTABLECONTENT:"",
        HBASEPARTITION:"",
        HBASETYPE:"",
        HBASEUSER:"",
        HTMLHBASENAMESPACE:"",
        HTMLHBASETABLECONTENT:"",
        FHIRHBASENAMESPACE:"",
        FHIRHBASETABLECONTENT:"",
        CDAHBASENAMESPACE:"",
        CDAHBASETABLECONTENT:"",
        HBASECODE: "",
        HTMLORGSYSTEM: "",
        FHIRORGSYSTEM: "",
        CDAORGSYSTEM: "",
      },
      /*测试按钮加载状态*/
      testButtonLoading: {
        HTMLDBCODE:false,//HTML测试状态
        FHIRDBCODE:false, //FHIR测试状态
        CDADBCODE:false, //共享文档测试状态
        HBASECODE: false,
      },
      //有效的数据源集合（测试成功的）
      effectiveDataSource:new Set(),
      /*建表按钮加载状态*/
      tableButtonLoading: {
        //HTML
        HTMLDBTABLECONTENT:false,//普通版文档内容表
        HTMLDBTABLEDIC:false,//字典表
        HTMLDBTABLEINDEX:false,//索引表
        HTMLHBASETABLECONTENT:false,//hbase版文档内容表
        //FHIR
        FHIRDBTABLECONTENT:false,
        FHIRDBTABLEDIC:false,
        FHIRDBTABLEINDEX:false,
        FHIRHBASENAMESPACE:false,
        FHIRHBASETABLECONTENT:false,
        //共享文档
        CDADBTABLECONTENT:false,
        CDADBTABLEDIC:false,
        CDADBTABLEINDEX:false,
        CDAHBASENAMESPACE:false,
        CDAHBASETABLECONTENT:false
      },
      testStatus:{
        HTMLDBCODE:'0',//HTML测试状态
        FHIRDBCODE:'0', //FHIR测试状态
        CDADBCODE:'0', //共享文档测试状态
        HBASECODE: '0' //habse测试状态
      },
      //建表状态
      createTableStatus:{
        //HTML
        HTMLDBTABLECONTENT:'0',//普通版文档内容表
        HTMLDBTABLEDIC:'0',//字典表
        HTMLDBTABLEINDEX:'0',//索引表
        HTMLHBASETABLECONTENT:'0',//hbase版文档内容表
        //FHIR
        FHIRDBTABLECONTENT:'0',
        FHIRDBTABLEDIC:'0',
        FHIRDBTABLEINDEX:'0',
        FHIRHBASENAMESPACE:'0',
        FHIRHBASETABLECONTENT:'0',
        //共享文档
        CDADBTABLECONTENT:'0',
        CDADBTABLEDIC:'0',
        CDADBTABLEINDEX:'0',
        CDAHBASENAMESPACE:'0',
        CDAHBASETABLECONTENT:"0"
      },
      //配置版本
      configVersion:{
        htmlVersion:'0',//HTML配置版本（默认普通版）
        fhirVersion:'0', //FHIR配置版本（默认普通版）
        cdaVersion:'0' //共享文档配置版本（默认普通版）
      },
      dbConnectionList:[],
      HbaseConnectionList:[],
      //radio: '1'
      //hbase厂商类型
      hbaseType: [{
        value: 'xinghuan',
        label: this.$t('星环')
      }, {
        value: 'huawei',
        label: this.$t('华为')
      }],
      //HTML内容表选项
      // htmlContentTable: [],
      loading:true,
      //process.env.VUE_APP_BASE_API + "/common/upload", // 上传的图片服务器地址
      uploadFileUrl:process.env.VUE_APP_BASE_URL + "/docStorageConfig/uploadHbaseConfigFile",
      //机构名称
      forOrganName: [],
      affiliatedSystem:this.$t('隶属系统')
    }
  },
  created() {
    this.containerLoading = true;
    this.listDatabaseConnection();
    this.listHbaseConnection();
    this.getHbaseConfigFile();
    this.getOrgSystemsList();
  },
  methods: {
    //查询配置信息
    getConfigInfo(){
      this.containerLoading = true;
      this.$api( "dataInstance/docStorageConfig.getCollectConfigInfo").then(response => {
        response.data.forEach(i =>{
          let configItemForm=i.configItem.replace(/_/g,'')
          let configValue=i.configValue
          let remark=i.remark
          let configItemName=i.configItemName
          this.configInfoForm[configItemForm]=configValue
          this.configInfoForm[configItemForm+"REMARK"]=remark
          this.configInfoForm[configItemForm+"ITEMNAME"]=configItemName
          //初始化状态
          this.initStatus(i, configValue, configItemForm);
        })
        this.containerLoading = false;
        this.testConnectionInit("HBASE_CODE");
        this.testDataSourceInit('HTML_DB_CODE')
        this.testDataSourceInit("FHIR_DB_CODE");
        this.testDataSourceInit("CDA_DB_CODE");
      })
    },
    //初始化状态(按钮)
    initStatus(i, configValue, configItemForm) {
      //建表状态
      if(i.configItem.indexOf("DB_TABLE")>-1||i.configItem.indexOf("HBASE_TABLE")>-1){
        this.createTableStatus[configItemForm]=i.testStatus
      }
      //测试状态
      switch (i.configItem) {
        case "HTML_DB_CODE":
          this.changeConfigVersionAndStatus(configValue, "0")
          this.testStatus[configItemForm] = i.testStatus
          if(i.testStatus=='1'){
            this.effectiveDataSource.add(i.configValue)
          }
          break
        case "FHIR_DB_CODE":
          this.changeConfigVersionAndStatus(configValue, "1")
          this.testStatus[configItemForm] = i.testStatus
          if(i.testStatus=='1'){
            this.effectiveDataSource.add(i.configValue)
          }
          break
        case "CDA_DB_CODE":
          this.changeConfigVersionAndStatus(configValue, "2")
          this.testStatus[configItemForm] = i.testStatus
          if(i.testStatus=='1'){
            this.effectiveDataSource.add(i.configValue)
          }
          break
        case "HBASE_CODE":
          this.changeConfigVersionAndStatus(configValue, "3")
          this.testStatus[configItemForm] = i.testStatus
          if(i.testStatus=='1'){
            this.effectiveDataSource.add(i.configValue)
          }
          break
        default:
          break;
      }
    },
    //初始化建表状态
    initCreateTableStatus(i, configValue, configItemForm) {

    },
    //查询数据源列表
    listDatabaseConnection() {
      this.$api( "dataInstance/docStorageConfig.getDataSourceList").then(response => {
        this.dbConnectionList = response.data;
        this.getConfigInfo()
      })
    },
    listHbaseConnection() {
      this.$api( "dataInstance/docStorageConfig.getHbaseSourceList").then(response => {
        this.HbaseConnectionList = response.data;
      })
    },
    //数据源测试
    testDataSource(itemName){
      let params={}
      let itemFormName=itemName.replace(/_/g,'')
      this.testButtonLoading[itemFormName] = true
      this.dbConnectionList.forEach(i=>{
        if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
          params=i
          params["createTime"] = undefined;
          params["updateTime"] = undefined;
        }
      })
      params['configItem']=itemName
      this.$api( "dataInstance/docStorageConfig.testDataSource", params)
        .then(response => {
          if(response.code==200){
            this.$message.success(this.$t('成功'));
            this.testStatus[itemFormName]='1'
            this.effectiveDataSource.add(this.configInfoForm[itemFormName])
          }else {
            this.$message.error(response.msg);
            this.testStatus[itemFormName]='-1'
          }
        })
        .catch((e) => {
          this.testStatus[itemFormName]='-1'
          this.$message.error(e?.message || this.$t('测试失败'))
        })
        .finally(() => {
          this.testButtonLoading[itemFormName]=false
        })
    },
    //hbase源测试
    testHbaseConfig(){
      let params={
        hbaseType: this.configInfoForm.HBASETYPE,
        hbaseUser: this.configInfoForm.HBASEUSER,
        partitionsNum: this.configInfoForm.HBASEPARTITION,
      }
      this.testButtonLoading.HBASECODE=true
      this.$api( "dataInstance/docStorageConfig.testHbaseConfig", params)
        .then(response => {
          if(response.code==200){
            this.testStatus.HBASECODE='1'
            this.effectiveDataSource.add(this.configInfoForm.HBASECODE)
            this.$message.success(response.msg);
          }else {
            this.$message.error(response.msg);
            this.testStatus.HBASECODE='-1'
          }
        })
        .catch((e) => {
          this.testStatus.HBASECODE='-1'
          this.$message.error(e?.message || this.$t('测试失败'))
        })
        .finally(() => {
          this.testButtonLoading.HBASECODE=false
        })
    },
    //建表
    createTable(dataSourceItem,schemaItem,thisItem, isUseHBase){
      let errorMsg=this.$t('数据源测试未通过不能建表!!!')
      //若是文档内容表则需区分是否使用hbase建表
      if(dataSourceItem.indexOf("||")>-1){//文档内容表方式
        if (isUseHBase && this.configInfoForm[isUseHBase] == '1') {
          if(this.configVersion.htmlVersion==1 && this.testStatus.HBASECODE=='1'){//hbase
            dataSourceItem=dataSourceItem.split("||")[1]
            schemaItem=schemaItem.split("||")[1]
            thisItem=thisItem.split("||")[1]
          } else {
            errorMsg=this.$t('hbase测试未通过不能建表')
            this.$message.error(errorMsg);
            return;
          }
        } else {
          dataSourceItem=dataSourceItem.split("||")[0]
          schemaItem=schemaItem.split("||")[0]
          thisItem=thisItem.split("||")[0]
        }
      }
      let dataSourceFormItem=dataSourceItem.replace(/_/g,'')
      let schemaItemFormName=schemaItem.replace(/_/g,'')
      let thisItemFormName=thisItem.replace(/_/g,'')
      // alert('数据源连通状态为：'+this.testStatus[dataSourceFormItem])
      console.log('数据源连通状态为：'+this.testStatus[dataSourceFormItem]);
      if(this.testStatus[dataSourceFormItem]!='1'){
        this.$message.error(errorMsg);
        return
      }
      /* if( this.createTableStatus[thisItemFormName]=="1"){
          this.$message.warning("表已存在");
          return
          }*/
      this.tableButtonLoading[thisItemFormName]=true
      let tableName=this.configInfoForm[schemaItemFormName]+'.'+this.configInfoForm[thisItemFormName]
      let params={
        dataSourceItem:dataSourceItem,
        schemaItem:schemaItem,
        tableItem:thisItem,
        tableName:tableName,
      }
      this.$api( "dataInstance/docStorageConfig.createDocTable", params).then(response => {
        if(response.code==200){
          // this.$message.success(this.$t('成功'));
          this.$message.success(response.data);
          this.createTableStatus[thisItemFormName]="1"
        }else {
          this.$message.error(response.msg);
          this.createTableStatus[thisItemFormName]="-1"
        }
        this.tableButtonLoading[thisItemFormName]=false
      })
    },

    //查询hbase配置文件信息
    getHbaseConfigFile(){
      this.loading=true
      this.$api( "dataInstance/docStorageConfig.getHbaseConfigFile").then(response => {
        if(response.code=="200"){
          this.hbaseConfigFileList=response.data;
          this.loading=false
        }else {
          console.log("获取 HBase 配置文件失败!");
          this.loading=false
        }
      })
    },
    /**
     * 数据源改变时对配置版本进行变化（0：普通版，1：大数据版），以及重置状态
     * @param dbId
     * @param docType
     * @param itemFormName 项目表单名称，存在的情况为下拉选切换，而页面初始化不存在
     */
    changeConfigVersionAndStatus(dbId,docType,itemFormName){
      //改变配置版本
      let dbList= this.dbConnectionList
      let docDesc="";
      for(let i=0;i<dbList.length;i++) {
        let db=dbList[i]
        if (db.databaseConnectionId == dbId) {
          switch (docType) {
            case "0"://html
              if (bigDataType.includes(db.dbType)) {
                this.configVersion.htmlVersion = "1"
              } else {
                this.configVersion.htmlVersion = "0"
              }
              docDesc="HTML"
              break
            case "1"://fhir
              if (bigDataType.includes(db.dbType)) {
                this.configVersion.fhirVersion = "1"
              } else {
                this.configVersion.fhirVersion = "0"
              }
              docDesc="FHIR"
              break
            case "2"://cda
              if (bigDataType.includes(db.dbType)) {
                this.configVersion.cdaVersion = "1"
              } else {
                this.configVersion.cdaVersion = "0"
              }
              docDesc="CDA"
              break
          }
        }
      }
      //改变状态
      if(itemFormName){//存在的情况为下拉选切换，而页面初始化不存在
        //改变下拉选时改变当前测试状态
        /*if(this.effectiveDataSource.has(dbId)){
            this.testStatus[itemFormName]='1'
        }else {
            this.testStatus[itemFormName]='0'
        }*/
        //切换就设为未测试状态（即使测试成功也得再测试，测试后会保存以及加载缓存后台才能读到配置）
        this.testStatus[itemFormName]='0'
        //切换建表状态未未建表状态
        let createTableStatus=this.createTableStatus
        Object.keys(createTableStatus).forEach((key) => {
          if(key.indexOf(docDesc)>-1){
            createTableStatus[key]="0"
          }
        })
      }
    },
    //内容表建表状态展示
    contentTableStatusShow (dbContentTableFormItem,hbaseContentTableFormItem, isUseHBase) {
      if(!this.tableButtonLoading[dbContentTableFormItem]&&!this.tableButtonLoading[hbaseContentTableFormItem]){//建表加载状态完毕时
        // 判断是否使用HBase
        if (isUseHBase && this.configInfoForm[isUseHBase] && this.configInfoForm[isUseHBase] == '1') { // 使用Hbase
          // 判断HBase是否测试通过
          if (this.configVersion.htmlVersion=='1'&&this.testStatus.HBASECODE=='1') {
            if(this.createTableStatus[hbaseContentTableFormItem]=='1'){//成功
              return "success"
            }
            if(this.createTableStatus[hbaseContentTableFormItem]=='-1'){//失败
              return "error"
            }
          } else { // 使用了HBase，但是HBase测试不通过
            return "error"
          }
        }else{//普通数据库方式
          if(this.createTableStatus[dbContentTableFormItem]=='1'){//成功
            return "success"
          }
          if(this.createTableStatus[dbContentTableFormItem]=='-1'){//失败
            return "error"
          }
        }
      }
    },
    /**
     * 测试按钮样式改变
     */
    testButtonStyle(testItem) {
      switch (testItem) {
        case "HBASE_CODE":
          if(!this.testButtonLoading.HBASECODE&&this.testStatus.HBASECODE=='1'){
            return "success"
          }else {
            return "danger"
          }
        case "HTML_DB_CODE":
          if(!this.testButtonLoading.HTMLDBCODE&&this.testStatus.HTMLDBCODE=='1'){
            return "success"
          }else {
            return "danger"
          }
        case "FHIR_DB_CODE":
          if(!this.testButtonLoading.FHIRDBCODE&&this.testStatus.FHIRDBCODE=='1'){
            return "success"
          }else {
            return "danger"
          }
        case "CDA_DB_CODE":
          if(!this.testButtonLoading.CDADBCODE&&this.testStatus.CDADBCODE=='1'){
            return "success"
          }else {
            return "danger"
          }
      }
    },
    /**
     * 建表按钮样式改变
     */
    tableButtonStyle(testItem) {
      switch (testItem) {
        case "HTML_DB_TABLE_INDEX":
          if(!this.tableButtonLoading.HTMLDBTABLEINDEX&&this.createTableStatus.HTMLDBTABLEINDEX=='1'){
            return "primary"
          }else {
            return "danger"
          }
        case "HTML_DB_TABLE_DIC":
          if(!this.tableButtonLoading.HTMLDBTABLEDIC&&this.createTableStatus.HTMLDBTABLEDIC=='1'){
            return "primary"
          }else {
            return "danger"
          }
        case "FHIR_DB_TABLE_INDEX":
          if(!this.tableButtonLoading.FHIRDBTABLEINDEX&&this.createTableStatus.FHIRDBTABLEINDEX=='1'){
            return "primary"
          }else {
            return "danger"
          }
        case "FHIR_DB_TABLE_DIC":
          if(!this.tableButtonLoading.FHIRDBTABLEDIC&&this.createTableStatus.FHIRDBTABLEDIC=='1'){
            return "primary"
          }else {
            return "danger"
          }
        case "CDA_DB_TABLE_INDEX":
          if(!this.tableButtonLoading.CDADBTABLEINDEX&&this.createTableStatus.CDADBTABLEINDEX=='1'){
            return "primary"
          }else {
            return "danger"
          }
      }
    },
    handleSaveDataSource(docType) {
      switch (docType) {
        case 0: // HTML文档
          if (this.configInfoForm.HTMLUSEHBASE == '1') { // 判断是否需要是用HBase作为数据源
            if(this.configInfoForm.HBASECODE){ // 有选择 HBase 数据源才允许测试&保存
              let htmlParam = {
                HTMLDBCODE: this.configInfoForm.HTMLDBCODE,
                HTMLDBSCHEMA: this.configInfoForm.HTMLDBSCHEMA,
                HTMLDBTABLECONTENT: this.configInfoForm.HTMLDBTABLECONTENT,
                HTMLDBTABLEDIC: this.configInfoForm.HTMLDBTABLEDIC,
                HTMLDBTABLEINDEX: this.configInfoForm.HTMLDBTABLEINDEX,

                HTMLHBASENAMESPACE: this.configInfoForm.HTMLHBASENAMESPACE,
                HTMLHBASETABLECONTENT: this.configInfoForm.HTMLHBASETABLECONTENT,
                HTMLUSEHBASE: this.configInfoForm.HTMLUSEHBASE,
                HBASECODE: this.configInfoForm.HBASECODE,
                HTMLORGSYSTEM: this.configInfoForm.HTMLORGSYSTEM,
              }
              let params={}
              let itemFormName='HBASECODE'.replace(/_/g,'')
              this.testButtonLoading[itemFormName] = true;
              this.HbaseConnectionList.forEach(i=>{
                if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
                  params=i
                }
              })
              this.$api("dataInstance/docStorageConfig.testHbaseConfig", params)
                .then((response) => {
                  if (response.code == 200) {
                    this.testStatus.HBASECODE = '1'
                    this.effectiveDataSource.add(this.configInfoForm[itemFormName])
                    return this.$api( "dataInstance/docStorageConfig.saveDataSource", htmlParam)
                  } else {
                    this.testStatus.HBASECODE = '-1'
                    throw new Error(this.$t("保存失败，hbase测试未通过，请检查hbase数据源是否正确！"))
                  }
                })
                .then(res => {
                  if(res.code == 200){
                    this.$message.success(this.$t('保存成功'))
                  } else {
                    this.$message.error(res.msg)
                  }
                })
                .catch((e) => {
                  this.$message.error(e?.message || this.$t('保存失败'))
                })
                .finally(() => {
                  this.testButtonLoading[itemFormName] = false
                })
            }else {
              this.$message.warning(this.$t('如果HTML文档需要使用HBase作为文档内容存储来源，需要先测试HBase数据源连接是否正常！'));
            }
          } else {
            let htmlParam = {
              HTMLDBCODE: this.configInfoForm.HTMLDBCODE,
              HTMLDBSCHEMA: this.configInfoForm.HTMLDBSCHEMA,
              HTMLDBTABLECONTENT: this.configInfoForm.HTMLDBTABLECONTENT,
              HTMLDBTABLEDIC: this.configInfoForm.HTMLDBTABLEDIC,
              HTMLDBTABLEINDEX: this.configInfoForm.HTMLDBTABLEINDEX,
              HTMLUSEHBASE: this.configInfoForm.HTMLUSEHBASE,
              HTMLORGSYSTEM: this.configInfoForm.HTMLORGSYSTEM,
            }
            this.$api( "dataInstance/docStorageConfig.saveDataSource", htmlParam).then(res => {
              if(res.code == 200){
                this.$message.success(this.$t('保存成功'))
              } else {
                this.$message.error(res.msg)
              }
            })
          }
          break;
        case 1: // FHIR文档
          if (this.configInfoForm.FHIRUSEHBASE == '1') { // 判断是否需要是用HBase作为数据源
            if(!this.testButtonLoading.HBASECODE&&this.testStatus.HBASECODE=='1'){ // 判断Hbase数据源测试是否通过
              let fhirParam = {
                FHIRDBCODE: this.configInfoForm.FHIRDBCODE,
                FHIRDBSCHEMA: this.configInfoForm.FHIRDBSCHEMA,
                FHIRDBTABLECONTENT: this.configInfoForm.FHIRDBTABLECONTENT,
                FHIRDBTABLEDIC: this.configInfoForm.FHIRDBTABLEDIC,
                FHIRDBTABLEINDEX: this.configInfoForm.FHIRDBTABLEINDEX,

                FHIRHBASENAMESPACE: this.configInfoForm.FHIRHBASENAMESPACE,
                FHIRHBASETABLECONTENT: this.configInfoForm.FHIRHBASETABLECONTENT,
                FHIRUSEHBASE: this.configInfoForm.FHIRUSEHBASE,
                HBASECODE: this.configInfoForm.HBASECODE,
                FHIRORGSYSTEM: this.configInfoForm.FHIRORGSYSTEM,
              }
              let params={}
              let itemFormName='HBASECODE'.replace(/_/g,'')
              this.testButtonLoading[itemFormName] = true;
              this.HbaseConnectionList.forEach(i=>{
                if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
                  params=i
                }
              })
              this.$api("dataInstance/docStorageConfig.testHbaseConfig", params)
                .then((response) => {
                  if (response.code == 200) {
                    this.testStatus.HBASECODE = '1'
                    this.effectiveDataSource.add(this.configInfoForm[itemFormName])
                    return this.$api( "dataInstance/docStorageConfig.saveDataSource", fhirParam)
                  } else {
                    this.testStatus.HBASECODE = '-1'
                    throw new Error(this.$t("保存失败，hbase测试未通过，请检查hbase数据源是否正确！"))
                  }
                })
                .then(res => {
                  if(res.code == 200){
                    this.$message.success(this.$t('保存成功'))
                  } else {
                    this.$message.error(res.msg)
                  }
                })
                .catch((e) => {
                  this.$message.error(e?.message || this.$t('保存失败'))
                })
                .finally(() => {
                  this.testButtonLoading[itemFormName] = false
                })
            }else {
              this.$message.warning(this.$t('如果FHIR文档需要使用HBase作为文档内容存储来源，需要先测试HBase数据源连接是否正常！'));
            }
          } else {
            let fhirParam = {
              FHIRDBCODE: this.configInfoForm.FHIRDBCODE,
              FHIRDBSCHEMA: this.configInfoForm.FHIRDBSCHEMA,
              FHIRDBTABLECONTENT: this.configInfoForm.FHIRDBTABLECONTENT,
              FHIRDBTABLEDIC: this.configInfoForm.FHIRDBTABLEDIC,
              FHIRDBTABLEINDEX: this.configInfoForm.FHIRDBTABLEINDEX,
              FHIRUSEHBASE: this.configInfoForm.FHIRUSEHBASE,
              FHIRORGSYSTEM: this.configInfoForm.FHIRORGSYSTEM,
            }
            this.$api( "dataInstance/docStorageConfig.saveDataSource", fhirParam).then(res => {
              if(res.code == 200){
                this.$message.success(this.$t('保存成功'))
              } else {
                this.$message.error(res.msg)
              }
            })
          }
          break;
        case 2: // 共享文档
          if (this.configInfoForm.CDAUSEHBASE == '1') { // 判断是否需要是用HBase作为数据源
            if(!this.testButtonLoading.HBASECODE&&this.testStatus.HBASECODE=='1'){ // 判断Hbase数据源测试是否通过
              let cdaParam = {
                CDADBCODE: this.configInfoForm.CDADBCODE,
                CDADBSCHEMA: this.configInfoForm.CDADBSCHEMA,
                CDADBTABLECONTENT: this.configInfoForm.CDADBTABLECONTENT,
                CDADBTABLEDIC: this.configInfoForm.CDADBTABLEDIC,
                CDADBTABLEINDEX: this.configInfoForm.CDADBTABLEINDEX,

                CDAHBASENAMESPACE: this.configInfoForm.CDAHBASENAMESPACE,
                CDAHBASETABLECONTENT: this.configInfoForm.CDAHBASETABLECONTENT,
                CDAUSEHBASE: this.configInfoForm.CDAUSEHBASE,
                HBASECODE: this.configInfoForm.HBASECODE,
                CDAORGSYSTEM: this.configInfoForm.CDAORGSYSTEM,
              }
              let params={}
              let itemFormName='HBASECODE'.replace(/_/g,'')
              this.testButtonLoading[itemFormName] = true;
              this.HbaseConnectionList.forEach(i=>{
                if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
                  params=i
                }
              })
              this.$api("dataInstance/docStorageConfig.testHbaseConfig", params)
                .then((response) => {
                  if (response.code == 200) {
                    this.testStatus.HBASECODE = '1'
                    this.effectiveDataSource.add(this.configInfoForm[itemFormName])
                    return this.$api( "dataInstance/docStorageConfig.saveDataSource", cdaParam)
                  } else {
                    this.testStatus.HBASECODE = '-1'
                    throw new Error(this.$t("保存失败，hbase测试未通过，请检查hbase数据源是否正确！"))
                  }
                })
                .then(res => {
                  if(res.code == 200){
                    this.$message.success(this.$t('保存成功'))
                  } else {
                    this.$message.error(res.msg)
                  }
                })
                .catch((e) => {
                  this.$message.error(e?.message || this.$t('保存失败'))
                })
                .finally(() => {
                  this.testButtonLoading[itemFormName] = false
                })
            }else {
              this.$message.warning(this.$t('如果共享文档需要使用HBase作为文档内容存储来源，需要先测试HBase数据源连接是否正常！'));
            }
          } else {
            let cdaParam = {
              CDADBCODE: this.configInfoForm.CDADBCODE,
              CDADBSCHEMA: this.configInfoForm.CDADBSCHEMA,
              CDADBTABLECONTENT: this.configInfoForm.CDADBTABLECONTENT,
              CDADBTABLEDIC: this.configInfoForm.CDADBTABLEDIC,
              CDADBTABLEINDEX: this.configInfoForm.CDADBTABLEINDEX,
              CDAUSEHBASE: this.configInfoForm.CDAUSEHBASE,
              CDAORGSYSTEM: this.configInfoForm.CDAORGSYSTEM,
            }
            this.$api( "dataInstance/docStorageConfig.saveDataSource", cdaParam).then(res => {
              if(res.code == 200){
                this.$message.success(this.$t('保存成功'))
              } else {
                this.$message.error(res.msg)
              }
            })
          }
          break;
      }
    },
    changeUseHBase(docType, label) {
      console.log(docType, label);
    },
    testConnection(itemName,docType){
      let params={}
      let itemFormName=itemName.replace(/_/g,'')
      this.testButtonLoading[itemFormName] = true;
      this.HbaseConnectionList.forEach(i=>{
        if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
          params=i
        }
      })
      this.$api("dataInstance/docStorageConfig.testHbaseConfig", params)
        .then((response) => {
          if (response.code == 200) {
            this.$message.success("测试成功");
            this.testStatus.HBASECODE = '1';
            this.effectiveDataSource.add(this.configInfoForm[itemFormName])
          } else {
            this.$message.error("测试失败:" + response.msg);
            this.testStatus.HBASECODE = '-1';
          }
        })
        .catch((e) => {
          this.testStatus.HBASECODE = '-1';
          this.$message.error(e?.message || this.$t('测试失败'))
        })
        .finally(() => {
          this.testButtonLoading[itemFormName] = false;
        })
    },
    testConnectionInit(itemName,docType){
      let params={}
      let itemFormName=itemName.replace(/_/g,'')
      this.testButtonLoading[itemFormName] = true;
      this.HbaseConnectionList.forEach(i=>{
        if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
          params=i
        }
      })
      this.$api("dataInstance/docStorageConfig.testHbaseConfig", params)
        .then((response) => {
          if (response.code == 200) {
            this.testStatus.HBASECODE = '1';
            this.effectiveDataSource.add(this.configInfoForm[itemFormName])
          } else {
            this.testStatus.HBASECODE = '-1';
            if(docType == 'html'){
              this.createTableStatus.HTMLDBTABLECONTENT = '-1';
              this.createTableStatus.HTMLDBTABLEDIC = '-1';
              this.createTableStatus.HTMLDBTABLEINDEX = '-1';
              this.createTableStatus.HTMLHBASETABLECONTENT = '-1';
            }
            if(docType == 'fhir'){
              this.createTableStatus.FHIRDBTABLECONTENT = '-1';
              this.createTableStatus.FHIRDBTABLEDIC = '-1';
              this.createTableStatus.FHIRDBTABLEINDEX = '-1';
              this.createTableStatus.FHIRHBASENAMESPACE = '-1';
              this.createTableStatus.FHIRHBASETABLECONTENT = '-1';
            }
            if(docType == 'cda'){
              this.createTableStatus.CDADBTABLECONTENT = '-1';
              this.createTableStatus.CDADBTABLEDIC = '-1';
              this.createTableStatus.CDADBTABLEINDEX = '-1';
              this.createTableStatus.CDAHBASENAMESPACE = '-1';
              this.createTableStatus.CDAHBASETABLECONTENT = '-1';
            }
          }
        })
        .catch(() => {
          this.testStatus.HBASECODE = '-1';
        })
        .finally(() => {
          this.testButtonLoading[itemFormName] = false;
        })
    },
    testDataSourceInit(itemName){
      let params={}
      let itemFormName=itemName.replace(/_/g,'')
      this.testButtonLoading[itemFormName] = true
      this.dbConnectionList.forEach(i=>{
        if(i.databaseConnectionId==this.configInfoForm[itemFormName]){
          params=i
          params["createTime"] = undefined;
          params["updateTime"] = undefined;
        }
      })
      params['configItem']=itemName
      this.$api( "dataInstance/docStorageConfig.testDataSource", params)
        .then(response => {
          if(response.code==200){
            this.testStatus[itemFormName]='1'
            this.effectiveDataSource.add(this.configInfoForm[itemFormName])
          }else {
            // this.$message.error(response.msg);
            this.testStatus[itemFormName]='-1'
            if(itemName == 'HTML_DB_CODE'){
              this.createTableStatus.HTMLDBTABLECONTENT = '-1';
              this.createTableStatus.HTMLDBTABLEDIC = '-1';
              this.createTableStatus.HTMLDBTABLEINDEX = '-1';
              this.createTableStatus.HTMLHBASETABLECONTENT = '-1';
            }
            if(itemName == 'FHIR_DB_CODE'){
              this.createTableStatus.FHIRDBTABLECONTENT = '-1';
              this.createTableStatus.FHIRDBTABLEDIC = '-1';
              this.createTableStatus.FHIRDBTABLEINDEX = '-1';
              this.createTableStatus.FHIRHBASENAMESPACE = '-1';
              this.createTableStatus.FHIRHBASETABLECONTENT = '-1';
            }
            if(itemName == 'CDA_DB_CODE'){
              this.createTableStatus.CDADBTABLECONTENT = '-1';
              this.createTableStatus.CDADBTABLEDIC = '-1';
              this.createTableStatus.CDADBTABLEINDEX = '-1';
              this.createTableStatus.CDAHBASENAMESPACE = '-1';
              this.createTableStatus.CDAHBASETABLECONTENT = '-1';
            }
          }
        })
        .catch(() => {
          this.testStatus[itemFormName]='-1'
        })
        .finally(() => {
          this.testButtonLoading[itemFormName]=false
        })
    },
    //查询机构信息
    getOrgSystemsList(){
      this.$api( "dataInstance/docStorageConfig.getOrgSystemsList").then(response => {
        this.forOrganName = response.data;
      })
    },
  },


}

</script>
<style type="scss" scoped>
.config-header-title{
  height:40px !important;
  line-height:40px;
  font-size:14px;
  border-top: 1px solid #dfe4ed;
  background-color: #fff;
  /*border-bottom: 1px solid #dfe4ed*/
}
.dataSource-select-inner{
  width:60%
}
.default-select-inner{
  width:36%
}
.default-input-inner {
  width:36%;
}
.hbase-default-input {
  width:20%;
}
.hbase-default-input.hos-input-number.is-controls-right .hos-input__inner {
  text-align: left;
}
label{
  color:grey;
}
.test-button{
  float: right;
}
.app-container {
  overflow-y: auto;
  min-height: calc(100% - 20px);
  height: auto;
}
</style>
